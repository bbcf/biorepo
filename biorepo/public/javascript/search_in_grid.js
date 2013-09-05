
$(document).ready(function() {

    /* Init the table */
    var oTable = $('.grid').dataTable( {
        "bStateSave": true,
        "sPaginationType": "scrolling",
        "iDisplayLength": 50,
        "aLengthMenu": [[50, 100, 250, -1], [50, 100, 250, "All"]]
    });
    /* new FixedHeader( oTable ); */


    // /* $('.row_selected') */
    // /* customize interface searchpage*/
    // $('.dataTables_info').first().remove();
    // /*$('.dataTables_paginate').first().remove();*/
    // $('.paging_two_button').first().remove();

} );


