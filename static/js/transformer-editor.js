$(document).ready(function () {
	var mime = 'text/x-mariadb';

	// get mime type
	if (window.location.href.indexOf('mime=') > -1) {
		mime = window.location.href.substr(window.location.href.indexOf('mime=') + 5);
	}

	window.editor = CodeMirror.fromTextArea(document.getElementById('code'), {
			mode: mime,
			indentWithTabs: true,
			smartIndent: true,
			lineWrapping: true,
			lineNumbers: true,
			matchBrackets : true,
			autofocus: true
	});
});
