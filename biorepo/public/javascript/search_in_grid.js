
$(document).ready(function() {

    /* Init the table */
    var oTable = $('.grid').dataTable( {
        "oLanguage": { "sSearch": "" },
        "bStateSave": true,
        /*"sPaginationType": "scrolling",*/
        "iDisplayLength": 50,
        "aLengthMenu": [[50, 100, 250, -1], [50, 100, 250, "All"]]

    });
    /* new FixedHeader( oTable ); */

    $('.dataTables_filter input').attr("placeholder", "Search here...");
    $('.dataTables_filter input').addClass("form-control");
    $('.dataTables_filter input').attr('id',"searchField");

    // /* $('.row_selected') */
    // /* customize interface searchpage*/
    // $('.dataTables_info').first().remove();
    // /*$('.dataTables_paginate').first().remove();*/
    // $('.paging_two_button').first().remove();

} );


