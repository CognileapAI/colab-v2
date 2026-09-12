// Audit only: literal JSX classes and stylesheet reachability. Missing classes are candidates, not defects.
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
const root = process.cwd();
const require = createRequire(path.join(root, 'frontend/package.json'));
const ts = require('typescript');
const postcss = require('postcss');
const base = path.join(root, 'frontend/src');
const rel = f => path.relative(root, f);
const walk = d => fs.readdirSync(d, {withFileTypes:true}).flatMap(e => e.isDirectory() ? walk(path.join(d,e.name)) : [path.join(d,e.name)]);
const files = walk(base);
const cssFiles = files.filter(f => f.endsWith('.css'));
const codeFiles = files.filter(f => /\.tsx?$/.test(f));
const definitions = new Map();
const rules = [];
for (const file of cssFiles) {
  postcss.parse(fs.readFileSync(file,'utf8'), {from:file}).walkRules(rule => {
    const classes = [...rule.selector.matchAll(/\.([a-zA-Z_][\w-]*)/g)].map(m => m[1]);
    const data = {file:rel(file),line:rule.source.start.line,selector:rule.selector};
    rules.push(data);
    for (const c of new Set(classes)) definitions.set(c,[...(definitions.get(c) ?? []),data]);
  });
}
const usages = [], dynamic = [], controls = [], imports = new Map(), jsxFiles=[];
for (const file of cssFiles) {
  const edges=[];
  postcss.parse(fs.readFileSync(file,'utf8'), {from:file}).walkAtRules('import',rule=>{
    const value=rule.params.match(/^["']([^"']+)["']/)?.[1];
    if(value?.startsWith('.')) {
      const target=path.resolve(path.dirname(file),value);
      edges.push({specifier:value,target:fs.existsSync(target)?rel(target):null,line:rule.source.start.line});
    }
  });
  imports.set(rel(file),edges);
}
function stringValues(node) {
  if (!node) return [];
  if (ts.isStringLiteralLike(node)) return [node.text];
  if (ts.isConditionalExpression(node)) return [...stringValues(node.whenTrue),...stringValues(node.whenFalse)];
  if (ts.isParenthesizedExpression(node)) return stringValues(node.expression);
  if (ts.isBinaryExpression(node) && [ts.SyntaxKind.BarBarToken,ts.SyntaxKind.AmpersandAmpersandToken,ts.SyntaxKind.QuestionQuestionToken].includes(node.operatorToken.kind)) return [...stringValues(node.left),...stringValues(node.right)];
  return [];
}
for (const file of codeFiles) {
  const source = ts.createSourceFile(file, fs.readFileSync(file,'utf8'), ts.ScriptTarget.Latest,true,file.endsWith('.tsx') ? ts.ScriptKind.TSX : ts.ScriptKind.TS);
  if(file.endsWith('.tsx')) jsxFiles.push(rel(file));
  const edges=[];
  const line=n=>source.getLineAndCharacterOfPosition(n.getStart(source)).line+1;
  function visit(n) {
    if(ts.isImportDeclaration(n) && ts.isStringLiteral(n.moduleSpecifier)) {
      const value=n.moduleSpecifier.text;
      if(value.startsWith('.')) {
        const target=path.resolve(path.dirname(file),value);
        const found=[target,target+'.tsx',target+'.ts',path.join(target,'index.tsx'),path.join(target,'index.ts')].find(p=>fs.existsSync(p)&&fs.statSync(p).isFile());
        edges.push({specifier:value,target:found?rel(found):null,line:line(n)});
      }
    }
    if(ts.isJsxOpeningElement(n)||ts.isJsxSelfClosingElement(n)) {
      const tag=n.tagName.getText(source);
      const attr=n.attributes.properties.find(a=>ts.isJsxAttribute(a)&&a.name.getText(source)==='className');
      const expr=attr?.initializer && ts.isJsxExpression(attr.initializer) ? attr.initializer.expression : attr?.initializer;
      const values=stringValues(expr);
      if(attr && !values.length) dynamic.push({file:rel(file),line:line(n),tag,expression:expr?.getText(source)});
      for(const value of values) for(const cls of value.split(/\s+/).filter(Boolean)) usages.push({file:rel(file),line:line(n),tag,class:cls,defined:definitions.has(cls)});
      if(['button','select','input','textarea'].includes(tag)) controls.push({file:rel(file),line:line(n),tag,className:expr?.getText(source)??null});
    }
    ts.forEachChild(n,visit);
  }
  visit(source); imports.set(rel(file),edges);
}
const reachable=new Set();
function reach(file) {if(reachable.has(file))return;reachable.add(file);for(const e of imports.get(file)??[])if(e.target)reach(e.target);}
reach('frontend/src/main.tsx');
const missing=usages.filter(u=>!u.defined);
const result={
  scope:{cssFiles:cssFiles.map(rel),tsxFiles:jsxFiles,tsFiles:codeFiles.length,cssCount:cssFiles.length,tsxCount:jsxFiles.length},
  summary:{definedClassNames:definitions.size,literalClassOccurrences:usages.length,missingClassNames:new Set(missing.map(u=>u.class)).size,missingOccurrences:missing.length,dynamicExpressions:dynamic.length,nativeControls:controls.length,controlsWithoutClass:controls.filter(c=>!c.className).length},
  missingCandidates:missing,dynamicExpressions:dynamic,nativeControls:controls,
  cssReachability:cssFiles.map(f=>({file:rel(f),reachableFromMain:reachable.has(rel(f)),importedBy:[...imports].filter(([,es])=>es.some(e=>e.target===rel(f))).map(([f])=>f)})),
  unreachableTsx:jsxFiles.filter(f=>!reachable.has(f)),
  definitions:Object.fromEntries(definitions),usages,imports:Object.fromEntries(imports),
  limitations:['Literal JSX class expressions only; unresolved template/identifier expressions are listed separately.','Selector presence does not establish DOM match, cascade precedence, or visible styling.','Reachability uses static relative JS imports and relative quoted CSS @import; eager stylesheet loading can make a missing local import harmless.','Classes may be semantic/test hooks styled by tag or ancestor selectors.'],
};
console.log(JSON.stringify(result,null,2));
