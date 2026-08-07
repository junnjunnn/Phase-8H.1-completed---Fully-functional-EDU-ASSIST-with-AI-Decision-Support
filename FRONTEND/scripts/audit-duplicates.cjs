const fs = require('fs')
const path = require('path')
const root = path.join(__dirname, '..', 'src')
const routeFile = path.join(root, 'routes', 'AppRoutes.jsx')
let routesText = ''
try {
  routesText = fs.readFileSync(routeFile, 'utf8')
} catch (e) {
  console.error('Could not read AppRoutes.jsx', e.message)
  process.exit(2)
}
const pathRe = /path=\"([^\"]+)\"/g
let m
const paths = []
while ((m = pathRe.exec(routesText)) !== null) paths.push(m[1])
const dups = {}
paths.forEach(p => dups[p] = (dups[p] || 0) + 1)
const duplicateRoutes = Object.fromEntries(Object.entries(dups).filter(([k,v])=>v>1))
console.log('duplicate_routes:', JSON.stringify(duplicateRoutes, null, 2))

const compDefs = {}
function walk(dir){
  for (const name of fs.readdirSync(dir)){
    const fp = path.join(dir, name)
    const stat = fs.statSync(fp)
    if (stat.isDirectory()) walk(fp)
    else if (fp.endsWith('.jsx')){
      const txt = fs.readFileSync(fp, 'utf8')
      const re = /export(?: default)?\s+(?:function|const|class)\s+([A-Za-z0-9_]+)/g
      let mm
      while ((mm = re.exec(txt)) !== null){
        compDefs[mm[1]] = compDefs[mm[1]] || []
        compDefs[mm[1]].push(path.relative(path.join(__dirname,'..'), fp))
      }
    }
  }
}
walk(root)
const duplicateExports = Object.fromEntries(Object.entries(compDefs).filter(([k,v])=>v.length>1))
console.log('duplicate_exported_names:', JSON.stringify(duplicateExports, null, 2))

// Check for missing exports referenced in AppRoutes imports
const importRe = /import \{\s*([A-Za-z0-9_,\s]+)\s*\}\s*from\s*['\"]([^'\"]+)['\"]/g
const missingExports = []
while ((m = importRe.exec(routesText)) !== null){
  const names = m[1].split(',').map(s=>s.trim())
  const rel = m[2]
  for (const name of names){
    const found = Object.entries(compDefs).some(([exportName, list]) => exportName === name && list.length>0)
    if (!found) missingExports.push({name, importFrom: rel})
  }
}
console.log('missing_exports:', JSON.stringify(missingExports, null, 2))
