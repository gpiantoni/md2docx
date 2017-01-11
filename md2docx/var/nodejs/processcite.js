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
var postCitat = [];
var items = [];

for (let i0 in citations_j) {
	var cit_items = citations_j[i0]['citationItems'];
	for (let i1 in cit_items) {
	 items.push(cit_items[i1]['id']);
 };
};

citeproc.updateItems(items);

for (let item in citations_j) {
try {
 postCitat.push([citations_j[item]['citationID'], 0]);
} catch (err) {
 console.error(citations_j[item]['citationID'])
};
}

for (let item in citations_j) {
try {
 postCitat.shift();
 var result = citeproc.appendCitationCluster(citations_j[item], preCitat, postCitat);
 j_format.push(result[0][1]);
 preCitat.push([result[0][2], 0]);


} catch (err) {
 console.error(citations_j[item]['citationID'])
};
}
fs.writeFileSync(outFile, JSON.stringify(j_format, null, 4));

// output references
var out_bib = citeproc.makeBibliography()
fs.writeFileSync(refFile, out_bib[1].join(''));
