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
            $('#table').html( '<table cellpadding="0" cellspacing="0" class="table table-striped table-bordered table-hover" border="0" class="display" id="datatableView"></table>' );

            var typeMapper = {number: 'numeric', string: 'string', date: 'date'};
            var aoColumns = [];
            for  (var i=0;i<data.H.length;i++) {
                var col = data.H[i];
                aoColumns.push({sTitle: col.label || col.id, sType: typeMapper[col.type] || 'string'});
            }

            var aaData = [];
            for  (var i=0;i<data.K.length;i++) {
                var row = $.map(data.K[i].c, function(val) {
                   return val.v;
                });

                aaData.push(row);
            }

           var oTable =  $('#datatableView').dataTable( {
                aaData: aaData,
                aoColumns: aoColumns
            });

            $('.dataTables_wrapper').each(function(){
                var datatable = $(this);
                // SEARCH - Add the placeholder for Search and Turn this into in-line formcontrol
                var search_input = datatable.closest('.dataTables_wrapper').find('div[id$=_filter] input');
                search_input.attr('placeholder', 'Search')
                search_input.addClass('form-control input-small')
                search_input.css('width', '250px')

                // SEARCH CLEAR - Use an Icon
                var clear_input = datatable.closest('.dataTables_wrapper').find('div[id$=_filter] a');
                clear_input.html('<i class="icon-remove-circle icon-large"></i>')
                clear_input.css('margin-left', '5px')

                // LENGTH - Inline-Form control
                var length_sel = datatable.closest('.dataTables_wrapper').find('div[id$=_length] select');
                length_sel.addClass('form-control input-small')
                length_sel.css('width', '75px')

                // LENGTH - Info adjust location
                var length_sel = datatable.closest('.dataTables_wrapper').find('div[id$=_info]');
                length_sel.css('margin-top', '18px')
             });
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

    function showInfo(info) {
        drawTable(null);
        drawPieChart(null);
        drawAreaChart(null);
        drawBarCharts(null);

        $('#info-message').text(info);
        $('#info-dialog').fadeIn();
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

            $('.alert').fadeOut();

            $.ajax({
                type: $form.attr('method'),
                url: $form.attr('action') + '?gwiz_json',
                data: data
            }).done(function(data) {

                if (data && data.error) {
                    showError(data.error);
                } else if (data && data.info) {
                    showInfo(data.info);
                } else {
                    var vistabs = $('#vistabs');

                    vistabs.find('a:first').tab('show');

                    vistabs.find('a').click(function (e) {
                        e.preventDefault();
                        $(this).tab('show');
                    });

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

        return false;
    });
});

/* Set the defaults for DataTables initialisation */
$.extend( true, $.fn.dataTable.defaults, {
    "sDom": "<'row'<'col-6'l><'col-6'f>r>t<'row'<'col-6'i><'col-6'p>>",
	"sPaginationType": "bootstrap",
	"oLanguage": {
		"sLengthMenu": "_MENU_ records per page"
	}
} );


/* Default class modification */
$.extend( $.fn.dataTableExt.oStdClasses, {
	"sWrapper": "dataTables_wrapper form-inline"
} );


/* API method to get paging information */
$.fn.dataTableExt.oApi.fnPagingInfo = function ( oSettings )
{
	return {
		"iStart":         oSettings._iDisplayStart,
		"iEnd":           oSettings.fnDisplayEnd(),
		"iLength":        oSettings._iDisplayLength,
		"iTotal":         oSettings.fnRecordsTotal(),
		"iFilteredTotal": oSettings.fnRecordsDisplay(),
		"iPage":          oSettings._iDisplayLength === -1 ?
			0 : Math.ceil( oSettings._iDisplayStart / oSettings._iDisplayLength ),
		"iTotalPages":    oSettings._iDisplayLength === -1 ?
			0 : Math.ceil( oSettings.fnRecordsDisplay() / oSettings._iDisplayLength )
	};
};


/* Bootstrap style pagination control */
$.extend( $.fn.dataTableExt.oPagination, {
	"bootstrap": {
		"fnInit": function( oSettings, nPaging, fnDraw ) {
			var oLang = oSettings.oLanguage.oPaginate;
			var fnClickHandler = function ( e ) {
				e.preventDefault();
				if ( oSettings.oApi._fnPageChange(oSettings, e.data.action) ) {
					fnDraw( oSettings );
				}
			};

            $(nPaging).append(
                '<ul class="pagination">'+
                    '<li class="prev disabled">' +
                        '<a href="#">' +
                            '<i class="icon-double-angle-left"></i> '+
                            oLang.sPrevious+
                        '</a>' +
                    '</li>'+
                    '<li class="next disabled">' +
                        '<a href="#">'+oLang.sNext+
                            '<i class="icon-double-angle-right"></i>' +
                        '</a>' +
                    '</li>'+
                '</ul>'
            );
			var els = $('a', nPaging);
			$(els[0]).bind( 'click.DT', { action: "previous" }, fnClickHandler );
			$(els[1]).bind( 'click.DT', { action: "next" }, fnClickHandler );
		},

		"fnUpdate": function ( oSettings, fnDraw ) {
			var iListLength = 5;
			var oPaging = oSettings.oInstance.fnPagingInfo();
			var an = oSettings.aanFeatures.p;
			var i, ien, j, sClass, iStart, iEnd, iHalf=Math.floor(iListLength/2);

			if ( oPaging.iTotalPages < iListLength) {
				iStart = 1;
				iEnd = oPaging.iTotalPages;
			}
			else if ( oPaging.iPage <= iHalf ) {
				iStart = 1;
				iEnd = iListLength;
			} else if ( oPaging.iPage >= (oPaging.iTotalPages-iHalf) ) {
				iStart = oPaging.iTotalPages - iListLength + 1;
				iEnd = oPaging.iTotalPages;
			} else {
				iStart = oPaging.iPage - iHalf + 1;
				iEnd = iStart + iListLength - 1;
			}

			for ( i=0, ien=an.length ; i<ien ; i++ ) {
				// Remove the middle elements
				$('li:gt(0)', an[i]).filter(':not(:last)').remove();

				// Add the new list items and their event handlers
				for ( j=iStart ; j<=iEnd ; j++ ) {
					sClass = (j==oPaging.iPage+1) ? 'class="active"' : '';
					$('<li '+sClass+'><a href="#">'+j+'</a></li>')
						.insertBefore( $('li:last', an[i])[0] )
						.bind('click', function (e) {
							e.preventDefault();
							oSettings._iDisplayStart = (parseInt($('a', this).text(),10)-1) * oPaging.iLength;
							fnDraw( oSettings );
						} );
				}

				// Add / remove disabled classes from the static elements
				if ( oPaging.iPage === 0 ) {
					$('li:first', an[i]).addClass('disabled');
				} else {
					$('li:first', an[i]).removeClass('disabled');
				}

				if ( oPaging.iPage === oPaging.iTotalPages-1 || oPaging.iTotalPages === 0 ) {
					$('li:last', an[i]).addClass('disabled');
				} else {
					$('li:last', an[i]).removeClass('disabled');
				}
			}
		}
	}
} );


/*
 * TableTools Bootstrap compatibility
 * Required TableTools 2.1+
 */
if ( $.fn.DataTable.TableTools ) {
	// Set the classes that TableTools uses to something suitable for Bootstrap
	$.extend( true, $.fn.DataTable.TableTools.classes, {
		"container": "DTTT btn-group",
		"buttons": {
			"normal": "btn",
			"disabled": "disabled"
		},
		"collection": {
			"container": "DTTT_dropdown dropdown-menu",
			"buttons": {
				"normal": "",
				"disabled": "disabled"
			}
		},
		"print": {
			"info": "DTTT_print_info modal"
		},
		"select": {
			"row": "active"
		}
	} );

	// Have the collection use a bootstrap compatible dropdown
	$.extend( true, $.fn.DataTable.TableTools.DEFAULTS.oTags, {
		"collection": {
			"container": "ul",
			"button": "li",
			"liner": "a"
		}
	} );
}
