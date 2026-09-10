<?php
/**
 * historico.php - lee el historico para mostrarlo dentro de la aplicacion.
 *
 *   GET historico.php              -> JSON con las filas, la mas reciente primero
 *   GET historico.php?descargar=1  -> el CSV como descarga, para abrirlo en Excel
 *
 * El CSV en si NO es accesible desde la web (lo impide el .htaccess). Se sirve a
 * traves de este archivo para que la pagina pueda pintar la tabla y para que se
 * pueda descargar sin entrar por FTP.
 *
 * AVISO HONESTO, igual que en el resto del proyecto: esto NO tiene
 * autenticacion. La pantalla de acceso de la pagina no puede protegerlo, porque su
 * contrasena viaja dentro de la propia pagina y cualquiera la lee. O sea que quien
 * descubra esta direccion puede ver el historico entero. Se acepto a sabiendas: lo
 * que hay aqui son URL que acaban impresas en folletos publicos, nombres de pila y
 * fechas. Si algun dia hay que cerrarlo de verdad, la via es proteger la carpeta
 * con .htpasswd en el servidor; entonces esto queda protegido sin tocar una linea.
 */

declare(strict_types=1);

const ARCHIVO   = __DIR__ . '/historico.csv';
const SEPARADOR = ';';
const MAX_FILAS = 500;   // se muestran las mas recientes; el CSV completo se descarga

date_default_timezone_set('Europe/Madrid');

// ---------- descarga del CSV entero ----------
if (isset($_GET['descargar'])) {
    if (!is_file(ARCHIVO)) {
        http_response_code(404);
        header('Content-Type: text/plain; charset=utf-8');
        echo 'Todavia no hay historico.';
        exit;
    }
    header('Content-Type: text/csv; charset=utf-8');
    header('Content-Disposition: attachment; filename="historico-qr-versus.csv"');
    header('Content-Length: ' . filesize(ARCHIVO));
    header('X-Content-Type-Options: nosniff');
    readfile(ARCHIVO);
    exit;
}

// ---------- listado en JSON ----------
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');

if (!is_file(ARCHIVO)) {
    echo json_encode(['ok' => true, 'total' => 0, 'filas' => []], JSON_UNESCAPED_UNICODE);
    exit;
}

$fh = @fopen(ARCHIVO, 'rb');
if ($fh === false) {
    http_response_code(500);
    echo json_encode(['ok' => false, 'error' => 'no se pudo leer el historico'], JSON_UNESCAPED_UNICODE);
    exit;
}

// Lectura con candado compartido: si alguien esta escribiendo justo ahora, se
// espera a que termine en vez de leer una fila a medio escribir.
@flock($fh, LOCK_SH);

$filas = [];
$primera = true;
while (($campos = fgetcsv($fh, 0, SEPARADOR)) !== false) {
    if ($campos === [null] || $campos === false) {
        continue;
    }
    if ($primera) {
        $primera = false;
        // La cabecera lleva el BOM pegado al primer campo; se detecta por su nombre.
        if (isset($campos[0]) && strpos($campos[0], 'fecha') !== false) {
            continue;
        }
    }
    if (count($campos) < 2 || $campos[1] === '') {
        continue;
    }
    $filas[] = [
        'fecha'    => $campos[0] ?? '',
        'url'      => $campos[1] ?? '',
        'quien'    => $campos[2] ?? '',
        'logo'     => $campos[3] ?? '',
        'tamano'   => $campos[4] ?? '',
        'formato'  => $campos[5] ?? '',
        'veredicto' => $campos[6] ?? '',
    ];
}

@flock($fh, LOCK_UN);
fclose($fh);

$total = count($filas);
$filas = array_reverse($filas);                 // la mas reciente primero
if ($total > MAX_FILAS) {
    $filas = array_slice($filas, 0, MAX_FILAS);
}

echo json_encode(
    ['ok' => true, 'total' => $total, 'mostradas' => count($filas), 'filas' => $filas],
    JSON_UNESCAPED_UNICODE
);
