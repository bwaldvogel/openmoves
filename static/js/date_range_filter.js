function init_date_range_pickers(start_date, end_date, page_name) {
    // Date time picker configuration
    $('#dtp_start').datetimepicker({
        defaultDate: start_date,
        maxDate: end_date,
        format: 'LL',          // http://momentjs.com/docs/#/displaying/format/
        calendarWeeks: true,
        showTodayButton: true
    });
    $('#dtp_end').datetimepicker({
        defaultDate: end_date,
        minDate: start_date,
        format: 'LL',          // http://momentjs.com/docs/#/displaying/format/
        calendarWeeks: true,
        showTodayButton: true
    });

    // Linked date time pickers: http://eonasdan.github.io/bootstrap-datetimepicker/#linked-pickers
    $("#dtp_start").on("dp.change",function (e) {
        reload_page_with_date($('#dtp_start').data("DateTimePicker").date(), $('#dtp_end').data("DateTimePicker").date(), page_name);
    });
    $("#dtp_end").on("dp.change",function (e) {
        reload_page_with_date($('#dtp_start').data("DateTimePicker").date(), $('#dtp_end').data("DateTimePicker").date(), page_name);
    });

    $(".dropdown-menu li a").click(function(){
      $(this).parents(".dropdown").find('.btn').find('.selection').text($(this).text());
      var start_date = null;
      switch($(this).text()) {
          case "1 week":
              start_date = moment().subtract(1, 'weeks');
              break;
          case "1 month":
              start_date = moment().subtract(1, 'months');
              break;
          case "2 months":
              start_date = moment().subtract(2, 'months');
              break;
          case "6 months":
              start_date = moment().subtract(6, 'months');
              break;
          case "1 year":
              start_date = moment().subtract(1, 'years');
              break;
          case "all moves":
              start_date = moment().year(1970).month(0).date(1);
              break;
          default:
              start_date = moment().subtract(1, 'months');
              break;
       }
       reload_page_with_date(start_date, moment(), page_name);
    });
}

function init_date_range_dropdown(start_date, end_date) {
    // Pre-select the date time period dropdown by the selected date range
    var start_date = moment(start_date);
    var end_date = moment(end_date);
    // Determine configured time period
    var period = "custom";
    if(start_date.isSame(moment(end_date).subtract(1, 'weeks').startOf('day'))) {
        period = "1 week";
    }
    else if(start_date.isSame(moment(end_date).subtract(1, 'months').startOf('day'))) {
        period = "1 month";
    }
    else if(start_date.isSame(moment(end_date).subtract(2, 'months').startOf('day'))) {
        period = "2 months";
    }
    else if(start_date.isSame(moment(end_date).subtract(6, 'months').startOf('day'))) {
        period = "6 months";
    }
    else if(start_date.isSame(moment(end_date).subtract(1, 'years').startOf('day'))) {
        period = "1 year";
    }
    else if(start_date.isSame(moment().year(1970).month(0).date(1).startOf('day'))) {
        period = "all moves";
    }
    $(".dropdown").find('.btn').find('.selection').text(period);
}

function reload_page_with_date(start_date, end_date, page_name) {
    var newLocation = window.location.href;
    newLocation = updateUrlParameter(newLocation, 'start_date', start_date.format('YYYY-MM-DD'));
    newLocation = updateUrlParameter(newLocation, 'end_date', end_date.format('YYYY-MM-DD'));
    window.location.href = newLocation;
}

// https://gist.github.com/niyazpk/f8ac616f181f6042d1e0
// Add / Update a key-value pair in the URL query parameters
function updateUrlParameter(uri, key, value) {
    // remove the hash part before operating on the uri
    var i = uri.indexOf('#');
    var hash = i === -1 ? ''  : uri.substr(i);
         uri = i === -1 ? uri : uri.substr(0, i);

    var re = new RegExp("([?&])" + key + "=.*?(&|$)", "i");
    var separator = uri.indexOf('?') !== -1 ? "&" : "?";
    if (uri.match(re)) {
        uri = uri.replace(re, '$1' + key + "=" + value + '$2');
    } else {
        uri = uri + separator + key + "=" + value;
    }
    return uri + hash;  // finally append the hash as well
}
