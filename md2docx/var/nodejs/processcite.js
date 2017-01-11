var path = require('path');
var fs = require('fs');
var CSL = require('./citeproc.js').CSL;

// input files (+ 'locales-en-US.xml')
workDir = process.argv[2];
bibFile = process.argv[3];
cslFile = process.argv[4];
localeDir = process.argv[5];

citationsFile = path.format({dir: workDir, base: 'citations.json'});

// output files 
outFile = path.format({dir: workDir, base: 'formattedCitations.json'});
refFile = path.format({dir: workDir, base: 'formattedReferences.txt'});

// read in files
var CSLStyle = fs.readFileSync(cslFile, 'utf8');
var bib = JSON.parse(fs.readFileSync(bibFile, 'utf8'));
var citations_j = JSON.parse(fs.readFileSync(citationsFile, 'utf8'));

// prepare CSL engine
citeprocSys = {
 retrieveLocale: function (lang){
	localesFile = path.format({dir: localeDir, 
	                           base: 'locales-' + lang + '.xml'});
	return fs.readFileSync(localesFile, 'utf8');
 },
 retrieveItem: function(id){
	return bib[id];
 }
};

var citeproc = new CSL.Engine(citeprocSys, CSLStyle);

// output citations
var j_format = [];
var preCitat = [];

for (let item in citations_j) {
try {
 var result = citeproc.processCitationCluster(citations_j[item], preCitat, []);
 j_format.push(result[1][0][1]);
 preCitat.push([result[1][0][2], 0]);
} catch (err) {
 console.error(citations_j[item])
};
}
fs.writeFileSync(outFile, JSON.stringify(j_format, null, 4));

// output references
var out_bib = citeproc.makeBibliography()
fs.writeFileSync(refFile, out_bib[1].join(''));
