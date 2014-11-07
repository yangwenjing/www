(function(exports, $, _){
  "use strict";

  $.fn.postLink = function(params){
    var link = this.get(0);
    var $form = $('<form method="post" action="' + link.href + '"></form>');
    for( var param in params ){
      if( params.hasOwnProperty(param) ){
        $form.append('<input type="hidden" name="' + param + '" value="' + params[param] + '" />');
      }
    }
    $form.appendTo($('body')).submit();
  };

  $.fn.highlightChange = function(duration){
    this.each(function(idx, ele){
      $(ele).css('background-color', '#ffc').animate({
        'background-color': '#fff'
      }, duration || 1500);
    });
  };

  /*
   * 将列转换为行
   * @param {jQuery=} table: 要转换的 table
   * @param {list=} retainRows: 要保留的列
   * @param {list=} transformRows: 要转换的列
   *
   */
  exports.transformTable = function(table, retainRows, transformRows){
    var trList = table.children('tbody').children('tr');
    if( !trList.length ) { return; }

    var count = trList.children('td').length;
    if( !count ) { return; }

    var rowIndex = retainRows.concat(transformRows);
//    var rowIndex = transformRows.concat(retainRows);

    // 得到一个多维数组
    var values = trList.map(function(idx, tr){
      var rowList = $(tr).children('td').map(function(idx, td){
        return td.innerText;
      });

      // 按照 retainRows 和 transformRows 重排 values
      return _.sortBy(rowList, function(value, _idx){
        var sort = rowIndex.indexOf(_idx);
        return sort > -1 ? sort : _idx + 100000;
      });
    });

    // 一层层的 groupBy
    _.range(values[0].length).map(function(idx){
    });

    var last_value = [];
    for (var i =0; i < values.length; i ++ ) {
      var row = values[i];
      var rowKey = row.slice(0, retainRows.length).toString();
      if ( rowKey !== last_value ) {
        last_value = rowKey;
      }
    }

  };

  $(function() {

    $('a.post-link').click(function (event) {
      event.preventDefault();

      if ( confirm($(this).attr('data-confirm')) ) {
        var token = /csrftoken=([^;]+)/.exec(document.cookie)[1];

        $(this).postLink({
          csrfmiddlewaretoken: token
        });
      }

    });

    $('a[title]').tooltip();

  });
})(window, window.jQuery, window._);

