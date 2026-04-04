/**
 * 宝塔等面板可能在网站根目录（如 dist/）下放 .user.ini；
 * Vite 清空 outDir 时会失败（ENOTDIR）。构建前尽量删掉该文件。
 */
import { execFileSync } from 'node:child_process'
import { existsSync, unlinkSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { platform } from 'node:os'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const iniPath = join(__dirname, '..', 'dist', '.user.ini')

if (!existsSync(iniPath)) {
  process.exit(0)
}

if (platform() === 'linux') {
  try {
    execFileSync('chattr', ['-i', iniPath], { stdio: 'ignore' })
  } catch {
    /* 无 chattr 或无 +i 属性时忽略 */
  }
}

try {
  unlinkSync(iniPath)
} catch (err) {
  console.warn('[clean-dist-user-ini] 无法删除 dist/.user.ini:', err.message)
  console.warn('可在服务器上手动执行: chattr -i dist/.user.ini && rm -f dist/.user.ini')
  process.exit(1)
}
