import { mkdirSync, readFileSync, statSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const PNG_SIGNATURE = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
const MAX_BYTES = 1024 * 1024;
const MAX_DIM = 1024;

function verifyPng(data: Buffer): { width: number; height: number } {
  if (data.length < 24 || !data.subarray(0, 8).equals(PNG_SIGNATURE)) {
    throw new Error('entry.png is not a valid PNG file');
  }
  if (data.length > MAX_BYTES) {
    throw new Error(`entry.png exceeds 1 MiB limit (${data.length} bytes)`);
  }
  const width = data.readUInt32BE(16);
  const height = data.readUInt32BE(20);
  if (width === 0 || height === 0 || width > MAX_DIM || height > MAX_DIM) {
    throw new Error(`entry.png dimensions ${width}x${height} exceed ${MAX_DIM}x${MAX_DIM}`);
  }
  return { width, height };
}

function main(): void {
  const here = dirname(fileURLToPath(import.meta.url));
  const srcPath = join(here, 'entry.png');
  const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';
  const dstPath = join(outDir, 'entry.png');

  const size = statSync(srcPath).size;
  const payload = readFileSync(srcPath);
  if (payload.length !== size) {
    throw new Error(`entry.png size mismatch: stat=${size}, read=${payload.length}`);
  }
  const { width, height } = verifyPng(payload);

  mkdirSync(outDir, { recursive: true });
  writeFileSync(dstPath, payload);
  console.log(`Copied ${srcPath} -> ${dstPath} (${width}x${height}, ${size} bytes)`);
}

main();
