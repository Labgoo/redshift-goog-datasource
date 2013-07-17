google.load('visualization', '1', {packages:['table', 'corechart']});
google.setOnLoadCallback(function() {});

jQuery(function () {
	var mime = 'text/x-cooladatasql';

	window.editor = CodeMirror.fromTextArea(document.getElementById('sql'), {
			mode: mime,
			indentWithTabs: true,
			smartIndent: true,
			lineWrapping: true,
			lineNumbers: true,
			matchBrackets : true,
			autofocus: true
	});

    $('.CodeMirror').resizable({
        handles: 's, n',
        minHeight: 200,
        resize: function() {
            editor.setSize($(this).width(), $(this).height());
        }
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
		$('#sql-save-execute').prop('disabled', !hasQueryName()).toggleClass('disabled', !hasName);
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
        if (data) {
            var table = new google.visualization.Table($('#table')[0]);
            table.draw(data, {showRowNumber: true, page: 'enable', pageSize: 20});
        } else {
            $('#table').empty();
        }
    }

    function drawPieChart(data) {
        var chart = new google.visualization.PieChart($('#piechart')[0]);
        chart.draw(data);
    }

    function drawAreaChart(data) {
        var chart = new google.visualization.AreaChart($('#areachart')[0]);
        chart.draw(data);
    }

    function drawBarCharts(data) {
        var chart = new google.visualization.BarChart($('#barcharts')[0]);
        chart.draw(data);
    }

    function hasQueryName() {
        var queryName = $.trim($('#query-name').val());
        return queryName.length > 0;
    }

    function showError(error) {
        drawTable(null);
        drawPieChart(null);
        drawAreaChart(null);
        drawBarCharts(null);

        $('#error-message').text(error);
        $('#error-dialog').fadeIn();
    }

    $("#sql-execute, #sql-save-execute").click(function() {
    	if (recreateVars) {
			createVarsFills();
			return false;
		}

        var $btn = $(this);
        $btn.addClass('loading');

        $('i', $btn).addClass('icon-spinner icon-spin');

        var newQuery = $('form').data('new-query');

        if (!newQuery || !hasQueryName()) {
            var $form = $('form');

            window.editor.save();

            var data = $form.serializeArray();

            data.push({ name: this.name, value: this.value });

            $.ajax({
                type: $form.attr('method'),
                url: $form.attr('action') + '?gwiz_json',
                data: data
            }).done(function(data) {
                if (data && data.error) {
                    showError(data.error);
                } else {
                    $('#vistabs a:first').tab('show');

                    $('#vistabs a').click(function (e) {
                        e.preventDefault();
                        $(this).tab('show');
                    });

                    $('#error-dialog').fadeOut();

                    if (data) {
                        var json_data = new google.visualization.DataTable(data, 0.6);

                        drawTable(json_data);
                        drawPieChart(json_data);
                        drawAreaChart(json_data);
                        drawBarCharts(json_data);
                    }
                }
            }).always(function() {
                $btn.removeClass('loading');
                $('i', $btn).removeClass('icon-spinner icon-spin');
            }).fail(function(jqXHR, textStatus, errorThrown) {
                showError(errorThrown);
            });

            return false;
        }
    });
});
