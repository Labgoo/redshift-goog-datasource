// these keywords are used by all SQL dialects (however, a mode can still overwrite it)
var sqlKeywords = "alter and as asc between by count create delete desc distinct drop from having in insert into is join like not on or order select set table union update values where ";

// turn a space-separated list into an array
function set(str) {
    var obj = {}, words = str.split(" ");
    for (var i = 0; i < words.length; ++i) obj[words[i]] = true;
    return obj;
}

// A generic SQL Mode. It's not a standard, it just try to support what is generally supported
CodeMirror.defineMIME("text/x-cooladatasql", {
    name: "sql",
    keywords: set(sqlKeywords),
    functions: set("path_to_string path_duration path_count first_event second_event"),
    builtin: set("bool boolean bit blob enum long longblob longtext medium mediumblob mediumint mediumtext time timestamp tinyblob tinyint tinytext text bigint int int1 int2 int3 int4 int8 integer float float4 float8 double char varbinary varchar varcharacter precision real date datetime year unsigned signed decimal numeric"),
    atoms: set("false true null unknown"),
    operatorChars: /^[*+\-%<>!=]/,
    dateSQL: set("date time timestamp"),
    support: set("ODBCdotTable doubleQuote binaryNumber hexNumber")
});
