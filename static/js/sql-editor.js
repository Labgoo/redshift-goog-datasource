$(document).ready(function () {
	var mime = 'text/x-mariadb';

	// get mime type
	if (window.location.href.indexOf('mime=') > -1) {
			mime = window.location.href.substr(window.location.href.indexOf('mime=') + 5);
	}

	window.editor = CodeMirror.fromTextArea(document.getElementById('sql'), {
			mode: mime,
			indentWithTabs: true,
			smartIndent: true,
			lineWrapping: true,
			lineNumbers: true,
			matchBrackets : true,
			autofocus: true
	});

	var recreateVars = false;

	var sheepItForm = $('#sheepItForm').sheepIt({
        separator: '',
        allowRemoveLast: true,
        allowRemoveCurrent: true,
        allowAdd: true,
        allowAddN: false,
        maxFormsCount: 10,
        minFormsCount: 0,
        iniFormsCount: 0,

		afterAdd: function(source, newForm) {
            recreateVars = true;
        },
        afterRemoveCurrent: function(source, removedForm) {
			var fieldName = $('.var-name', removedForm).val();
        	$('input[name=' + fieldName + ']').parents('.control-group').remove();
            recreateVars = true;
        }
    });

	$('#query-name').change(function() {
		var hasName = $.trim($(this).val()).length > 0;
		$('#sql-save-execute').prop('disabled', !hasName).toggleClass('disabled', !hasName);
	});

	$(document).on('change', '.var-name', function() {
		var varIndex = $(this).data('var-index');

		$("#dynfield" + varIndex).attr('name', $(this).val());
		$("#dynfield-label" + varIndex).text($(this).val());
	});

	function createVarsFills() {
		var inputs = $('.cloned-input');

		var field = '';

		inputs.each(function(i) {
			var name = $("#sheepItForm_" +  i + "_name").val();
			var type = $("#sheepItForm_" +  i + "_type").val();
			var defaultValue = $("#sheepItForm_" +  i + "_default").val();
			
			var fieldId = "dynfield" + i;
			var currentValue = $('input[name='+ name +']').val();

			var value = currentValue || defaultValue;

			field += '<div class="control-group">';
			field += '<label class="control-label" id="dynfield-label' + i +'"  for="' + fieldId + '" >' + name + '</label>';
			field += '<div class="controls">';
			if (type === 'string') {
				field += '<input class="input-xlarge" type="text" name="' + name + '" value="' + value + '" id="'+ fieldId +'"/>';
			} else if (type === 'integer') {
				field += '<input class="input-xlarge" type="text" name="' + name + '" value="' + value + '" id="'+ fieldId +'"/>';
			} else if (type === 'float') {
				field += '<input class="input-xlarge" type="text" name="' + name + '" value="' + value + '" id="'+ fieldId +'"/>';
			}
			
			field += "</div>";
			field += "</div>";
		});

		$('#vars').html($(field));

		recreateVars = false;
	};

    $("#sql-execute").click(function() {
    	if (recreateVars) {
			createVarsFills();
			return false;
		}
    });
});
