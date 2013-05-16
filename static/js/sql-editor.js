google.load('visualization', '1', {packages:['table', 'corechart']});
google.setOnLoadCallback(function() {});

jQuery(function () {
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

    function drawTable(data) {
        var table = new google.visualization.Table(document.getElementById('table'));
        table.draw(data, {showRowNumber: true});
    }

    function drawPieChart(data) {
        var chart = new google.visualization.PieChart(document.getElementById('piechart'));
        chart.draw(data);
    }

    function drawAreaChart(data) {
        var chart = new google.visualization.AreaChart(document.getElementById('areachart'));
        chart.draw(data);
    }

    function drawBarCharts(data) {
        var chart = new google.visualization.BarChart(document.getElementById('barcharts'));
        chart.draw(data);
    }

    $("#sql-execute, #sql-save-execute").click(function() {
    	if (recreateVars) {
			createVarsFills();
			return false;
		}

        var $btn = $(this);
        $btn.addClass('loading');

        var newQuery = $('form').data('new-query');

        if (!newQuery) {
            var $form = $('form');

            window.editor.save();

            var data = $form.serializeArray();

            data.push({ name: this.name, value: this.value });

            $.ajax({
                type: $form.attr('method'),
                url: $form.attr('action'),
                data: data
            }).done(function(data) {
                var json_data = new google.visualization.DataTable(data, 0.6);

                $('#vistabs a:first').tab('show');

                $('#vistabs a').click(function (e) {
                    e.preventDefault();
                    $(this).tab('show');
                });

                drawTable(json_data );
                drawPieChart(json_data);
                drawAreaChart(json_data);
                drawBarCharts(json_data);
            }).always(function() {
                $btn.removeClass('loading');
            }).fail(function(jqXHR, textStatus) {

            });

            return false;
        }
    });
});
