<?php
/**
 * registrar.php - historico de codigos QR generados. Sin base de datos.
 *
 * Anade una linea a historico.csv cada vez que alguien guarda un codigo desde
 * el generador. El archivo se abre en Excel y se descarga por FTP: NO es
 * accesible desde la web, lo impide el .htaccess que va al lado.
 *
 * Subir por FTP junto a index.html, en la misma carpeta.
 *
 * Nota honesta sobre a que aspira esto: es un endpoint interno sin
 * autenticacion. Quien descubra la direccion podria anadir lineas falsas. No se
 * protege con un token porque tendria que viajar dentro de la pagina y cualquiera
 * lo leeria, o sea que no protegeria nada. Lo que si esta acotado es el dano:
 * hay tope de tamano de archivo y tope por campo, asi que nadie puede llenar el
 * disco, y el CSV no se puede leer desde fuera. Si algun dia hace falta mas,
 * la via es proteger la carpeta entera con .htpasswd.
 */

declare(strict_types=1);

const ARCHIVO    = __DIR__ . '/historico.csv';
const MAX_BYTES  = 2097152;   // 2 MB: unas 20.000 lineas, de sobra
const MAX_CAMPO  = 500;       // caracteres por campo
const SEPARADOR  = ';';       // Excel en espanol espera punto y coma

header('Content-Type: application/json; charset=utf-8');
header('X-Content-Type-Options: nosniff');

function salir(int $codigo, string $error = ''): void
{
    http_response_code($codigo);
    echo json_encode(
        $error === '' ? ['ok' => true] : ['ok' => false, 'error' => $error],
        JSON_UNESCAPED_UNICODE
    );
    exit;
}

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    salir(405, 'solo POST');
}

if (is_file(ARCHIVO) && filesize(ARCHIVO) > MAX_BYTES) {
    // Nunca crecer sin limite. Cuando pase, se archiva el CSV y se empieza otro.
    salir(507, 'historico lleno, archivalo y vuelve a empezar');
}

function recortar(string $v, int $max): string
{
    return function_exists('mb_substr') ? mb_substr($v, 0, $max, 'UTF-8') : substr($v, 0, $max);
}

function campo(string $nombre): string
{
    $v = $_POST[$nombre] ?? '';
    if (!is_string($v)) {
        return '';
    }
    // Sin saltos de linea ni tabuladores: una fila es una linea.
    $v = str_replace(["\r", "\n", "\t"], ' ', $v);
    $v = trim(recortar($v, MAX_CAMPO));

    // Inyeccion de formulas: Excel EJECUTA una celda que empieza por = + - @, y
    // este archivo esta hecho para abrirse en Excel. Un apostrofo delante la
    // convierte en texto. Sin esto, una URL manipulada podria ejecutar algo en
    // el ordenador de quien abra el historico.
    if ($v !== '' && strpos('=+-@', $v[0]) !== false) {
        $v = "'" . $v;
    }
    return $v;
}

$cabecera = ['fecha', 'url', 'quien', 'logo', 'tamano', 'formato', 'escaneabilidad'];
$fila = [
    date('Y-m-d H:i:s'),
    campo('url'),
    campo('quien'),
    campo('logo'),
    campo('tamano'),
    campo('formato'),
    campo('veredicto'),
];

if ($fila[1] === '') {
    salir(400, 'falta la url');
}

$es_nuevo = !is_file(ARCHIVO);
$fh = @fopen(ARCHIVO, 'ab');
if ($fh === false) {
    salir(500, 'no se pudo escribir el historico');
}

if (flock($fh, LOCK_EX)) {
    if ($es_nuevo) {
        // BOM para que Excel reconozca UTF-8 y no destroce las tildes.
        fwrite($fh, "\xEF\xBB\xBF");
        fputcsv($fh, $cabecera, SEPARADOR);
    }
    fputcsv($fh, $fila, SEPARADOR);
    fflush($fh);
    flock($fh, LOCK_UN);
} else {
    fclose($fh);
    salir(503, 'historico ocupado, reintenta');
}

fclose($fh);
salir(200);
