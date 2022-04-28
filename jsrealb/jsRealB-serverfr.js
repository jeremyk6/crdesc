/// Simplistic node.js  jsRealBServer 
var http = require("http");
var url = require('url');
var fs = require('fs');

///////// 
//  load jsRealB file
const path=__dirname+'/jsRealB.js'
var jsRealB=require(path);

// "evaluate" the exports (Constructors for terminals and non-terminal) in the current context
// so that they can be used directly
for (var v in jsRealB){
    eval("var "+v+"=jsRealB."+v);
}

loadFr(true);
// eval(fs.readFileSync(__dirname+'/addLexicon-dme.js').toString());

// new lexicon entries
addToLexicon("pyramide", {"N":{"g":"f","tab":["n17"]}})
addToLexicon("viaduc", {"N":{"g":"m","tab":["n3"]}})
addToLexicon("croisement", {"N":{"g":"m","tab":["n3"]}})
addToLexicon("bus", {"N":{"g":"m","tab":["n3"]}})
addToLexicon("îlot", {"N":{"g":"m","tab":["n3"]}})
addToLexicon("tourne-à-gauche", {"N":{"g":"m","tab":["n3"]}})
addToLexicon("tourne-à-droite", {"N":{"g":"m","tab":["n3"]}})
addToLexicon("entrant", {"A":{"tab":["n28"]}})
addToLexicon("sortant", {"A":{"tab":["n28"]}})

http.createServer(function (request, response) {
   response.writeHead(200, {'Content-Type': 'text/plain; charset=UTF-8'});
   var req = url.parse(request.url, true);
   var query = req.query;
   var lang  = query.lang
   var exp   = query.exp
   if (lang=="fr"){
        let errorType,sentence;
        try {        
            if (exp.startsWith("{")){
                errorType="JSON";
                jsonExp=JSON.parse(exp);
                if (jsonExp["lang"]){ // check specified language in the JSON
                    if (jsonExp["lang"]!=lang){
                        response.end("specified language should be "+lang+" not "+jsonExp["lang"]);
                        jsonExp["lang"]=lang;
                    } else {
                        jsonExp["lang"]=lang;
                    }
                }
                sentence=fromJSON(jsonExp).toString();
            } else {
                errorType="jsRealB expression";
                sentence=eval(exp).toString();
            }
            response.end(sentence)
        } catch (e) {
            response.end(`${e}\nErroneous realization from ${errorType}`)
            if (errorType=="JSON"){
                try { // pretty-print if possible... i.e. not a JSON error
                    response.end(ppJSON(JSON.parse(input)))
                } catch(e){ // print line as is
                    response.end(input);
                }
            } else {
                response.end(input)
            }
        }
   } else {
       response.end('Language should be "fr", but '+lang+' received\n')
   }
}).listen(8081);
// Console will print the message
console.log('jsRealB server [built on %s] running at http://127.0.0.1:8081/',jsRealB_dateCreated);

/* 
start server with : node dist/jsRealB-server.js
try these examples in a browser
http://127.0.0.1:8081/?lang=en&exp=S(NP(D("the"),N("man")),VP(V("love")))
that should display:
The man loves.
*/
