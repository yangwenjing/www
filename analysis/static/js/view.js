var app = angular.module('sina');

//function pickColumns(rows, start_idx, length) {
function pickColumns(rows, columns) {
  return rows.map(function(row){
    return row.filter(function(_, idx){
      return columns.indexOf(idx) > -1;
    });
  });
}

function renderGraph(ele_id, type, rows, labels) {
  if ( !rows.length ) {
    return;
  }

  if (type === 'line') {
    renderLineGraph(ele_id, rows, labels, {
      showDatePicker: false
    });

  } else if (type === 'bar') {
    renderCompareGraph(ele_id, rows, labels[0].type, {
      title: labels[0].label
    });

  } else if (type === 'geo') {
    var provinceIdx = 0;
    var provinces = [
      "北京", "天津", "重庆", "河北", "山西", "辽宁", "吉林",
      "黑龙江", "江苏", "上海",
      "浙江", "安徽", "福建", "江西", "山东", "河南", "湖北",
      "湖南", "广东", "海南", "四川", "贵州", "云南", "陕西",
      "甘肃", "青海", "台湾", "内蒙古", "广西",
      "西藏", "宁夏", "新疆", "香港", "澳门"
    ];

    rows = rows.filter(function (row) {
      return provinces.indexOf(row[provinceIdx]) !== -1;
    });

    renderGeoGraph(ele_id, rows, {
      title: labels[0].label
    });
  }
}

app.directive('graph', ['$http', '$timeout', function ($http, $timeout) {
  "use strict";

  return {
    restrict: 'E',
    scope: {
      title: '=',
      url: '=',
      show: '=',
      type: '=',
      refresh: '='
    },
    template: '<div ng-if="loading">loading ... </div><div ng-if="error" ng-bind="error" class="text-danger"></div><div class="_inner" style="height:100%"></div>',
    link: function (scope, element, attrs) {
      scope.$watch('url', refresh);
      scope.$watch('show', render);

      var inner = element.find('._inner');

      var requests = 0;
      var cachedData = null;

      function refresh () {
        var url = scope.url;

        var defer = $http.get(url, {
          headers: {
            'X-Requested-With': 'XMLHttpRequest'
          }
        });

        requests ++;
        scope.loading = true;

        defer.success(function(data){
          cachedData = data;
          scope.error = '';
          render();

        }).error(function () {
          scope.error = '加载数据失败';

        }).finally(function () {
          requests --;
          scope.loading = requests !== 0;

          if ( scope.refresh && scope.refresh > 0 ) {
            // 自动刷新
            $timeout(refresh, scope.refresh > 1000*300 ? scope.refresh : 1000*300);
          }
        });
      }

      function render () {
        inner.empty();

        if (scope.show === false || cachedData === null) {
          return;
        }

        var type = scope.type;
        var data = cachedData;

        if (!data.rows.length) {
          scope.error = '没有数据';
          return;
        }

        var dimensions = data.columns.filter(function(column){
          return column.type === 'dimension' && ['date', 'datetime'].indexOf(column.data_type) === -1;
        });

        if (dimensions.length > 1) {
          scope.error = '维度过多无法画图';

        } else if (dimensions.length === 1 && dimensions[0].data_type === 'province' ) {
          type = type || 'geo';

        } else if (dimensions.length === 1 ) {
          type = type || 'bar';

        } else if (dimensions.length === 0 ) {
          type = type || 'line';
        }

        var dateDimension = data.columns.filter(function(column){
          return column.type === 'dimension' && ['date', 'datetime'].indexOf(column.data_type) > -1;
        });

        var properties = data.columns.filter(function(column, idx){
          return column.type === 'property';
        });

        var dateIdx = data.columns.indexOf(dateDimension[0]);
        var propIdx = data.columns.indexOf(properties[0]);
        var dimIdx = data.columns.indexOf(dimensions[0]);

        var start_id = new Date() - 0;
        var labels = [], columns;

        var graphCount = type === 'line' ? Math.ceil(properties.length / 2) : properties.length;

        console.log('type', type, 'graphCount', graphCount, 'properties', properties.length, 'height', inner.height());
        var height = inner.height() / graphCount;

        for( var i=0; i < graphCount; i++, start_id++ ) {
          var ele_id = 'graph-' + start_id;
          inner.append('<div style="height:' + height + 'px;width: 100%;" class="graph" id="' + ele_id + '"></div>');

          labels = properties.filter(function(prop, idx) {
            return type === 'line' ? idx >= i * 2 && idx <= i * 2 + 1 : idx === i;
          }).map(function (prop) {
            return {
              label: prop.name,
              type: prop.data_type
            };
          });

          if (type === 'line') {
            columns = [dateIdx, propIdx + i * 2, propIdx + i * 2 + 1];
            labels.splice(0, 0, {
              label: '时间',
              type: 'datetime'
            });
            renderGraph(ele_id, type, pickColumns(data.rows, columns), labels);

          } else if ( type === 'bar' ) {
            columns = [dimIdx, propIdx + i];
            renderGraph(ele_id, type, pickColumns(data.rows, columns), labels);

          } else if (type === 'geo' ) {
            columns = [dimIdx, propIdx + i];
            renderGraph(ele_id, type, pickColumns(data.rows, columns), labels);

          } else {
            scope.error = '不支持的图像类型: ' + (type || "没有匹配的图表类型");
            scope.error += "。所选字段:" + data.columns.map(function(column){return column.name;}).join(',');
            return;
          }
        }
      }

      scope.render = render;
    }
  };
}]);

app.directive('report', ['$http', '$timeout', function ($http, $timeout) {
 "use strict";

 return {
   restrict: 'E',
   scope: {
     title: '=',
     url: '=',
     show: '=',
     refresh: '='
   },
   template: '<div ng-if="loading">loading ... </div><div ng-if="error" ng-bind="error" class="text-danger"></div>' +
     '<table class="table table-bordered">' +
     '<thead><tr><th ng-repeat="h in columns" ng-bind="h.name"></th></tr></thead>' +
     '<tbody><tr ng-repeat="row in rows track by $index">' +
     '<td ng-repeat="d in row track by $index" ng-bind="d"></td>' +
     '</tr></tbody>' +
     '</table>',

   link: function (scope, element, attrs) {
     scope.$watch('url', render);

     function render() {
       if (scope.show === false) {
         return;
       }

       if (scope.loading === true) {
         return;
       }

       var url = scope.url;
       var defer = $http.get(url, {
         headers: {
           'X-Requested-With': 'XMLHttpRequest'
         }
       });

       scope.loading = true;

       defer.success(function (data) {
         var len = data.rows.length, format;

         if ( len === 0 ) {
           scope.error = "没有数据";
           return;
         }

         scope.columns = data.columns;
         scope.rows = data.rows;

         if (data.columns[0].data_type === "date") {
           if (data.rows[len - 1][0] - data.rows[0][0] >= 3600 * 24) {
             // 超过一天，使用 YYYY/MM/DD 的格式
             format = function (ts) {
               var d = new Date(ts * 1000);
               return (d.getFullYear()) + "/" + (d.getMonth() + 1) + '/' + d.getDate();
             };

           } else {
             // 一天内，使用 YYYY/MM/DD HH:MM
             format = function (ts) {
               var d = new Date(ts * 1000);
               var hour = d.getHours() >= 10 ? d.getHours() : '0' + d.getHours();
               var min = d.getMinutes() >= 10 ? d.getMinutes() : '0' + d.getMinutes();
               return (d.getFullYear()) + "/" + (d.getMonth() + 1) + '/' + d.getDate()+" "+hour + ":" + min;
             };
           }
           scope.rows = scope.rows.map(function (row) {
             var _row = row.slice(0);
             _row[0] = format(row[0]);
             return _row;
           });

         } else if (data.columns[0].data_type == 'time') {
           format = function (ts) {
             var d = new Date(ts * 1000);
             return d.getHours() + ":" + d.getMinutes();
           };

           scope.rows = scope.rows.map(function (row) {
             var _row = row.slice(0);
             _row[0] = format(row[0]);
             return _row;
           });
         }
       });

       defer.finally(function(){
         scope.loading = false;

         // 自动刷新
         if (scope.refresh && scope.refresh > 0) {
           $timeout(render, scope.refresh > 1000*300 ? scope.refresh : 1000*300);
         }

       });
     }

   }
 };
}]);
