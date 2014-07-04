
$(document).ready(function() {
    /* test tab opening into the grid*/
    var anOpen = [];
    var sImageUrl = "./images/";

    $('div.buttons').submit( function() {
        var sData = $('input', oTable.fnGetNodes()).serialize();
        alert( "The following data would have been submitted to the server: \n\n"+sData );
        return false;}
    );

    /* Init the table */
    /* Test time execution */
    // var start = new Date().getTime();
    var columns = $.parseJSON($('#columns').html());
    var oTable = $('.display_grid').dataTable( {
        "oLanguage": { "sSearch": "", "sProcessing": "Loading..." },
        "pagingType": "simple",

        "aoColumnDefs": [
            //{
                //"bVisible": false
                //"aTargets": searchlists[0]
            //},
            {
                "sClass": "control center", /* control the "info buton" into the grid */
                "aTargets": [0]
            }
            ], /* trono : 7 * aTargerts == hidden but searchable aTargets == hidden_positions*/
        "sDom": 'lfriptip',
        "bPaginate": true,
        "oColumnFilterWidgets": {
            sSeparator: "\\s*;+\\s*",
            //"aiExclude": searchlists[1],/* exclude "action column trono" research bouton field example : "aiExclude" == positions_not_searchable */
            "sPaginationType": "full_numbers"
        },
        "iDisplayLength": 50,
        "bDeferRender": true,
        "aLengthMenu": [[50, 100, 250, -1], [50, 100, 250, "All"]],
        "processing": true,
        "serverSide": true,
        "ajax": {
            url: "search_to_json"
        },
        "columns": columns,
        "createdRow": function ( row, data, index ) {
                            $(row).click( function() {
                                if ( $(this).hasClass('row_selected') ){
                                    $(this).removeClass('row_selected');
                                } else {
                                    $(this).addClass('row_selected');
                                    }
                            });
                        }
    });

    /* Add a click handler to the rows - this could be used as a callback */
    // $('.grid tbody tr').click( function() {
    //     if ( $(this).hasClass('row_selected') )
    //         $(this).removeClass('row_selected');
    //     else
    //         $(this).addClass('row_selected');

    // });


    /* $('.row_selected') */
    /* customize interface searchpage*/
    $('.dataTables_info').first().remove();
    /*$('.dataTables_paginate').first().remove();*/
    /*$('.paging_two_button').first().remove();*/
    $('.dataTables_paginate').first().remove();


    /* Actions buttons */
    /* DOWNLOAD BUTTON */
    // var dlButton = document.createElement("input");
    // dlButton.name ="dl";
    // dlButton.type = "submit";
    // dlButton.value ="Download";
    // console.log(XMLHttpRequest);
    // $(dlButton).click(function(){
    //     alert("Multi download button is not yet available");
    //     $.ajax({
    //         type: 'POST',
    //         url: "http://localhost:8080/biorepo/measurements/new",
    //         data: "meas_id="+getListIdSelected(),

    //         success: new XMLHttpRequest().getResponseHeader("Location")

    //     });

    //     return false;

    // });

    var createForm = document.createElement("form");
    createForm.id="form";
    // var end2 = new Date().getTime();
    // var time2 = end2 - start;
    // console.log('Execution total time: ' + time2 + ' ms');

    //get the selected measurement IDs onClick
    $(createForm).submit(function(e) {
       var m = getListIdSelected();
       return m, false;
    });

    /* UCSC BUTTON */
    var trackHubButton = document.createElement("input");
    trackHubButton.name = "ucsc";
    trackHubButton.type = "submit";
    trackHubButton.value ="Build UCSC TrackHub";
    $(trackHubButton).addClass("btn btn-success btn-sm");
    $(trackHubButton).click(function(){
        var measUCSC = getListIdSelected();
        if (measUCSC !== null){
        document.body.innerHTML+='<form id="formtemp" action="measurements/trackHubUCSC" method="POST">' +
            '<input id="meas_id" name="meas_id" type="hidden" value="' + measUCSC + '"/></form>';
        document.getElementById("formtemp").submit();
        // console.log(measUCSC);
        // $.ajax({
        //     type:'POST',
        //     url: "http://localhost:8080/measurements/trackHubUCSC",
        //     data : "meas_id="+measUCSC
        //});
        }
        else{
            alert("Select your measurements to build your UCSC trackhub please.");
        }

    });
    /* ucscButton.onClick(); */

    /* GDV BUTTON */
    // var gdvButton = document.createElement("input");
    // gdvButton.name = "gdv";
    // gdvButton.type = "submit";
    // gdvButton.value ="view in GDV";
    // $(gdvButton).click(function(){
    //     alert("GDV visualisation button is not yet available");
    // });
    /* gdvButton.onClick(); */

    /* UPLOAD CHILD BUTTON */
    var upButton = document.createElement("input");
    upButton.name = "upload";
    upButton.type = "submit";
    upButton.value = "Create new measurement from selected";
    $(upButton).addClass("btn btn-primary btn-sm");

    $(upButton).click(function(){
        var meas = getListIdSelected();

        document.body.innerHTML+='<form id="formtemp" action="measurements/new_with_parents" method="POST">' +
            '<input id="parents" name="parents" type="hidden" value="' + meas + '"/></form>';
        document.getElementById("formtemp").submit();
    });

    /* ZIP BUTTON */
    var zipButton = document.createElement("input");
    zipButton.name = "upload";
    zipButton.type = "submit";
    zipButton.value = "Get .zip";
    $(zipButton).addClass("btn btn-warning btn-sm");

    $(zipButton).click(function(){
        var meas = getListIdSelected();

        document.body.innerHTML+='<form id="formtemp" action="measurements/zipThem" method="POST">' +
            '<input id="list_meas" name="list_meas" type="hidden" value="' + meas + '"/></form>';
        document.getElementById("formtemp").submit();
    });

    /* CLONE BUTTON */
    var cloneButton = document.createElement("input");
    cloneButton.name = "clone";
    cloneButton.type = "submit";
    cloneButton.value = "Clone it";
    $(cloneButton).addClass("btn btn-danger btn-sm");

    $(cloneButton).click(function(){
        var meas = getListIdSelected();

        document.body.innerHTML+='<form id="formtemp" action="measurements/clone" method="POST">' +
            '<input id="clone" name="clone" type="hidden" value="' + meas + '"/></form>';
        document.getElementById("formtemp").submit();
    });





    var createDiv = document.createElement("div");
    var createDiv2 = document.createElement("div");
    createDiv.className="buttons";
    createDiv.textContent = "Possible action for selected rows : ";
    createDiv2.className="dataTables_buttons";

    createDiv2.appendChild(createForm);
    createForm.appendChild(createDiv);
    //createDiv.appendChild(dlButton);
    createDiv.appendChild(trackHubButton);
    createDiv.appendChild(upButton);
    createDiv.appendChild(zipButton);
    createDiv.appendChild(cloneButton);

    //to calculate widths of the search buttons
    // $.fn.textWidth = function(){
    //   var html_org = $(this).html();
    //   console.log(html_org);
    //   var html_calc = '<span>' + html_org + '</span>';
    //   $(this).html(html_calc);
    //   var width = $(this).find('span:first').width();
    //   $(this).html(html_org);
    //   return width;
    // };


    $.fn.textWidth = function(){
      var myObj = $(this);
      var valueContent = myObj.html();
      valueContent = '<span id="temporarySpanForWidth">' + valueContent + '</span>';
 
      var parentSelectElement = myObj.parent();
      parentSelectElement.before(valueContent);
      var temporarySpan = $("#temporarySpanForWidth");
      var myWidth = temporarySpan.width();
      temporarySpan.remove();
      return myWidth;
    };


    $(createDiv2).insertAfter('.dataTables_filter');
    $('.dataTables_filter input').attr("placeholder", "Search here...");
    $('.dataTables_filter input').addClass("form-control");
    $('.dataTables_filter input').attr('id',"searchField");
    //nice display with all the search buttons on top of search page
    $('.column-filter-widget > select').each(function(){
        var w = $(this).children().first().textWidth();
        $(this).css('width', w + 35 + 'px');
    });

    /* TEST SCROLL */
     $('.grid') .on('click','td.control', function (event){
        var parent = $(this).parent();
        var measu_id = parent.children().find('.id_meas').html();
        event.stopImmediatePropagation();
        var nTr = this.parentNode;
        var i = $.inArray( nTr, anOpen );
       if ( i === -1 ) {
          $('img', this).attr( 'src', sImageUrl+"close.png" );
           $.ajax({
            type: "POST",
            url: "measurements/info_display",
            data: {'meas_id': measu_id}
            }).done(function(data) {
                if (data.Error){
                    oTable.fnOpen( nTr, data.Error, 'details' );
                }
                else{
                    var sOut = '<div class="innerDetails">'+
                                '<table cellpadding="5" cellspacing="0" border="0" style="padding-left:50px;">';
                    for (var key in data) {
                        sOut = sOut + '<tr><td>'+ key +':</td><td>'+data[key]+'</td></tr>';
                    }
                    sOut = sOut + '</table>'+'</div>';
                    oTable.fnOpen( nTr, sOut, 'details' );
                }
                anOpen.push( nTr );

            });
        }
        else {
          $('img', this).attr( 'src', sImageUrl+"open.png" );
          oTable.fnClose( nTr );
          anOpen.splice( i, 1 );
        }
    } );

} );

function getListIdSelected()
{
    var listID = [];
    $('.row_selected').children().find('.id_meas').each(function(i){
        listID[i]=$(this).text();
    });

    if (listID.length !== 0){
        return listID;
    }
    else{
        return null;
    }
}
