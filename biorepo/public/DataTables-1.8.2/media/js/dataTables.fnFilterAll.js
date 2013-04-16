$.fn.dataTableExt.oApi.fnFilterAll = function(oSettings, sInput, iColumn, bRegex, bSmart) {
    if ( typeof bRegex == 'undefined' ) {
        bRegex = false;
    }

    if ( typeof bSmart == 'undefined' ) {
        bSmart = true;
    }

    for (var i in this.dataTableSettings) {
        jQuery.fn.dataTableExt.iApiIndex = i;
        this.fnFilter(sInput, iColumn, bRegex, bSmart);
    }
    jQuery.fn.dataTableExt.iApiIndex = 0;
}