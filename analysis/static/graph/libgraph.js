/**
 * Created by hongye.wei on 14-6-5.
 */

(function(exports, $, echarts, moment){
  "use strict";


  /*
   * divId: element id
   * labels: [{label: 'xxxx', type: 'one of nubmer,size,speed,time'}, ...]
   */
  function renderLineGraph(divId, rows, attrs, setting) {

    var defaultSetting = {
      showDatePicker: true,
      showSeriesMax: false,
      showSeriesAvg: false
    };

    var option = $.extend(true, defaultSetting, setting);
    var originAttrs = $.extend(true, [], attrs);

//    if (attrs[1].type === 'series') {
//      rows = sortFunction(rows);//rows按域名排序后，同域名内部再按时间排序
//      var copyAttrs = $.extend(true, [], attrs);
//      attrs = [copyAttrs[0]];
//      copyAttrs.splice(0, 2);
//
//      var series = [];//所有域名
//      for (var i = 0; i < rows.length; i++) {
//        var eachSeries = rows[i][1];
//        var index = series.indexOf(eachSeries);
//        if (index === -1) {//域名还未存在时
//          series.push(eachSeries);
//          for (var j = 0; j < copyAttrs.length; j++) {
//            var newLabel = eachSeries + '的' + copyAttrs[j].label;
//            var newAttr = {label: newLabel, type: copyAttrs[j].type};
//            attrs.push(newAttr);
//          }
//        }
//        rows[i].splice(1, 1);
//      }//end for
//
//      var step = rows.length / series.length; //每组数据长度，及x轴刻度总数
//
//      //将所有数据，按域名和时间划分变为只按时间划分的一组数据，对应于newAttrs
//      for (var i = 0; i < step; i++) { //组中的第几行
//        for (var j = 1; j < series.length; j++) {// 第几组域名
//          for (var k = 0; k < copyAttrs.length; k++) {
//            rows[i][rows[i].length] = rows[i + step * j][k + 1];
//          }
//        }
//      }
//      rows.splice(step);
//    }//end if (series)

    //处理及创建div容器
    var container = $("#" + divId);

    //若时间选择器不存在，则创建，若存在，则只需重建图表div
    if ((container).find(".date-picker").length === 0) {//未存在就创建
      container.empty();
      if (option.showDatePicker === true) {
        appendDataPicker(divId);
      }
    }
    else {//已存在
      if (option.showDatePicker === false) {
        container.empty();
      } else {
        (container).find(".graphic").remove();
      }
    }

    //div: graph
    var graphDiv = $('<div class="graphic" style="width: 100%;height:100%;"></div>');
    container.append(graphDiv);

    //处理数据
    var groups = getYData(attrs);//y轴数据
    var dates = [];//横轴日期
    var allYTypes = [];//y types
    var allYLabels = [];//y labels
    var labels = [];
    var height = graphDiv.height();//容器高度比
    var width = 100;//容器宽度比

    //获取所有Y轴attrs
    for (var i = 1; i < attrs.length; i++) {
      var support = formatYAxis[attrs[i].type];
      if (support !== undefined) {
        allYTypes.push(attrs[i].type);
      } else {
        console.log(attrs[i].type, "为不支持的类型,自动转为number型！");
        allYTypes.push('number');
      }
      allYLabels.push(attrs[i].label);
    }

    //获取时间数组
    if ( rows[1] && rows[1][0] - rows[0][0] < 86400) {//时间间隔小于一天，需再提取小时和分钟数
      dates = rows.map(function(row){
        var eachDate = new Date(row[0] * 1000);
        var minute = eachDate.getMinutes();
        if (minute < 10) {
          minute = '0' + minute;
        }
        var hour = eachDate.getHours();
        var day = eachDate.getDate();
        var month = eachDate.getMonth() + 1;
        return month + "/" + day + " " + hour + ":" + minute;
      });

    } else {
      dates = rows.map(function(row) {
        return moment(row[0] * 1000).format('M/DD');
      });
    }

    //获取每根Y轴的数据类型yType，获取每列y轴数据对应的y轴序号
    var yIndexs = [];
    var yTypes = [];
    for (var i = 0; i < allYTypes.length; i++) {
      var type = allYTypes[i];
      var yIndex = yTypes.indexOf(type);
      if (yIndex > -1) {
        yIndexs.push(yIndex);
      }
      else {
        yIndexs.push(yTypes.length);
        yTypes.push(type);
      }
    }

    var allYDatas = pickColumn(yTypes);
    var totalGragh = Math.ceil(yTypes.length / 2);
    var newheight = height;
    startGraph(totalGragh, yIndexs, dates, yTypes, labels, allYDatas,
      $.extend(true, [],option));//开始画图

    //开始画图：画图入口函数
    function startGraph(indexID, yIndexs, dates, yTypes, labels, allYDatas, option) {

      var newId = divId + indexID;
      indexID--;
      $("#" + divId).find(".graphic").append(
        $('<div id="' + newId + '"style="width' + width + '%;height:' + newheight + 'px;"></div>'));

      if (yTypes.length <= 2) {
        graphic(newId, yIndexs, dates, yTypes, labels, allYDatas, $.extend(true, [], option));

      } else {
        var newyTypes = yTypes.splice(0, 2);
        var yIndex = yIndexs.indexOf(2);
        var newLabels = labels.splice(0, yIndex);
        var newAllYDatas = allYDatas.splice(0, newLabels.length * dates.length);
        var newYIndexs = yIndexs.splice(0, yIndex);
        for (var i = 0; i < yIndexs.length; i++) {
          yIndexs[i] = yIndexs[i] - 2;
        }

        graphic(newId, newYIndexs, dates, newyTypes, newLabels, newAllYDatas, $.extend(true, [], option));
        startGraph(indexID, yIndexs, dates, yTypes, labels, allYDatas, option);
      }
    }

    //pickColumn()：传入y轴类型，返回按类型排序的y轴数据，且与y轴标记相对应
    function pickColumn(yTypes) {
      var allYData = [];
      for (var i = 0; i < yTypes.length; i++) {
        for (var j = 0; j < yIndexs.length; j++) {
          if (yIndexs[j] === i) {
            for (var a = 0; a < groups[j].length; a++) {
              allYData.push(groups[j][a]);
            }
            labels[labels.length] = allYLabels[j];
          }
        }
      }
      yIndexs.sort();
      return allYData;
    }

    //画图函数
    function graphic(newId, yIndexs, dates, yTypes, labels, allYDatas, option) {//x轴数据，Y轴类型，图例的label，y轴数据
      var myChart = echarts.init($('#'+newId)[0]);
      var lineChartsOption = {
        tooltip: {
          formatter: function (params) {
            var tipText = params[0][1];
            for (var i = 0; i < params.length; i++) {
              var tipText2 = "";
              var yType = yTypes[yIndexs[i]];
              tipText2 += '<br/>' + params[i][0] + ' : ' + formatYAxis[yType](params[i][2]);
              tipText += tipText2;
            }
            return tipText;
          },
          trigger: 'axis'
        },
        legend: {
          data: labels
        },
        toolbox: {
          show: true,
          feature: {
            saveAsImage: {
              show: true,
              title: '保存为图片',
              type: 'jpeg',
              lang: ['点击本地保存']
            },
            maxTool: {
              show: true,
              title: '最大值和最小值',
              icon: 'image://data:image/png;base64,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',
              onclick: function () {
                option.showSeriesMax = !(option.showSeriesMax);
                graphic(newId, yIndexs, dates, yTypes, labels, allYDatas, option);
              }
            },
            avgTool: {
              show: true,
              title: '平均线',
              icon: 'image://data:image/png;base64,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',
              onclick: function () {
                option['showSeriesAvg'] = !(option['showSeriesAvg']);
                graphic(newId, yIndexs, dates, yTypes, labels, allYDatas, option);
              }
            }
          }
        },
        calculable: true,//是否启用拖拽重计算特性
        xAxis: [
          {
            type: 'category',//横轴
            boundaryGap: false,//轴标签与轴是否有空隙（轴上false还是轴中间true）
            data: dates,
            axisLine: false
          }
        ],
        yAxis: getYAxis(yTypes),//传入y轴的类型数组
        series: getSeries(yIndexs, labels, allYDatas, yTypes, option)//传入series的label、data数组
      };

      if (dates.length > 7) {
        var dataZoom = {};
        dataZoom.show = true;
        dataZoom.realtime = true;
        dataZoom.start = 20;
        dataZoom.end = 80;
        lineChartsOption.dataZoom = dataZoom;
      }

      myChart.setOption(lineChartsOption);
    }

    function getYAxis(yTypes) {//传入y轴的类型数组，返回Y轴对应的设置
      var yAxisGroups = [];
      for (var i = 0; i < yTypes.length; i++) {
        var yType = yTypes[i];
        var yAxisItem = {};
        var axisLabelItem = {};
        axisLabelItem.formatter =
          (function (yType) {
            return function (v) {
              return formatYAxis[yType](v);
            };
          })(yType);

        yAxisItem.type = 'value';
        yAxisItem.axisLine = false;
        yAxisItem.axisLabel = axisLabelItem;
        if (yType !== "number") {
          yAxisItem.precision = 2;
        } else {
          yAxisItem.precision = 0;
        }
        yAxisItem.scale = true;
        if (yType === "percent") {
          yAxisItem.max = 100;
        }
        yAxisItem.boundaryGap = [0.05, 0.05];

        yAxisGroups.push(yAxisItem);
      }
      return yAxisGroups;
    }// end getYAxis()

    function getSeries(yIndexs, labels, allYDatas, yTypes, option) {//传入series的label、data数组
      //处理传入的y轴数据：一维数组变二维数组
      var yDatas = [];
      var len = allYDatas.length / labels.length;//每组数据的长度
      for (var i = 0; i < labels.length; i++) {
        var yData = [];
        for (var j = 0; j < len; j++) {
          yData.push(allYDatas[i * len + j]);
        }
        yDatas.push(yData);
      }

      //生成对应的series
      var seriesGroups = [];
      for (var i = 0; i < labels.length; i++) {
        var seriesItem = {};
        var itemStyleItem = {};
        var normalItem = {};
        var markPointItem = {};
        var markPointDataItem = [];
        var markLineItem = {};
        var markLineDataItem = [];
        var yType = yTypes[yIndexs[i]];

        if (option['showSeriesMax'] === true) {
          var emphasis = {
            label: {
              show: true,
              position: 'top',
              textStyle: {
                fontSize: '15',
                fontFamily: '微软雅黑',
                fontWeight: 'bold'
              },
              formatter: (function (yType) {
                return function (label, name, value) {
                  var tipText = label + '的' + name + ' : ' + formatYAxis[yType](value);
                  return tipText;
                }
              })(yType)
            }
          };
          var showLabel = {
            show: false
          };
          var showTooltip = {
            show: false
          };
          var maxMarkPoint = {
            type: 'max',
            name: '最大值',
            symbol: 'star',
            symbolSize: 12,
            tooltip: showTooltip,
            itemStyle: {
              normal: {
                color: 'green',
                label: showLabel
              },
              emphasis:  emphasis
            }
          };
          var minMarkPoint = {
            type: 'min',
            name: '最小值',
            symbol: 'pin',
            symbolSize : 7,
            tooltip: showTooltip,
            itemStyle: {
              normal: {
                color: 'red',
                label: showLabel
              },
              emphasis: emphasis
            }
          };
          markPointDataItem.push(maxMarkPoint);
          markPointDataItem.push(minMarkPoint);
        }//end if (showSeriesMax)

        markPointItem.data = markPointDataItem;
        seriesItem.markPoint = markPointItem;

        if (option['showSeriesAvg'] === true) {
          var svgMarkLine = {
            type: 'average',
            name: '平均值',
            tooltip: {
              show: false
            },
            itemStyle: {
              normal: {
                label: {
                  show: false
                }
              },
              emphasis: {
                label: {
                  show: true,
                  position: 'top',
                  textStyle: {
                    fontSize: '15',
                    fontFamily: '微软雅黑',
                    fontWeight: 'bold',
                    color: 'black'
                  },
                  formatter: (function(yType){
                    return function(label, name, value) {
                      var tipText = label + '的' + name  + formatYAxis[yType](value);;
                      return tipText;
                    }
                  })(yType)
                }
              }
            }
          };
          markLineDataItem.push(svgMarkLine);
        }//end if (showSeriesAvg)

        markLineItem.data = markLineDataItem;
        seriesItem.markLine = markLineItem;

        seriesItem.yAxisIndex = yIndexs[i];
        seriesItem.type = 'line';
        seriesItem.symbol = 'none';
        seriesItem.name = labels[i];
        itemStyleItem.normal = normalItem;
        seriesItem.itemStyle = itemStyleItem;
        seriesItem.data = yDatas[i];
        seriesGroups.push(seriesItem);
      }
      return seriesGroups;
    }//end getSeries()

    function getYData(attrs) {
      var groups = [];

      for (var i = 1; i < attrs.length; i++) {
        var group = [];
        for (var j = 0; j < rows.length; j++) {
          group.push(rows[j][i]);
        }
        groups.push(group);
      }
      return groups;
    }

    function sortFunction(array) {//二维数组排序
      return array.sort(function (x, y) {
        return (x[1] === y[1]) ? (x[0] - y[0]) : (x[1].localeCompare(y[1]));
      });
    }

    function appendDataPicker(parentId) {
      var dataPicker = $('<div></div>');
      $("#" + parentId).append(dataPicker);
      dataPicker.addClass("date-picker");
      dataPicker.css({
        'left': '0',
        'top': '0',
        'background': '#fff',
        'cursor': 'pointer',
        'padding': '5px 10px',
        'border': '1px solid #ccc',
        'position': 'absolute',
        'z-index': 10
      });
      dataPicker.html('<i class="glyphicon glyphicon-calendar fa fa-calendar"></i><span></span> <b class="caret"></b>');
      dataPicker.children("span").css({'padding-left': '5px '});
      dataPicker.children("span").html("最近7天");

      var cb = function (start, end, label) {
        dataPicker.children("span").html(label);
      };
      var optionSet1 = {
        startDate: moment().subtract('days', 6),
        endDate: moment(),
        minDate: '01/01/2012',
        maxDate: '12/31/2014',
        dateLimit: { days: 60 },
        showDropdowns: true,
        timePicker: false,
        timePickerIncrement: 1,
        timePicker12Hour: true,
        ranges: {
          '最近7天': [moment().subtract('days', 6), moment()],
          '最近30天': [moment().subtract('days', 29), moment()],
          '本月': [moment().startOf('month'), moment()],
          '上个月': [moment().subtract('month', 1).startOf('month'), moment().subtract('month', 1).endOf('month')]
        },
        opens: 'left',
        buttonClasses: ['btn btn-default'],
        applyClass: 'btn-small btn-primary',
        cancelClass: 'btn-small',
        format: 'MM/DD/YYYY',
        separator: ' to ',
        locale: {
          applyLabel: '确定',
          cancelLabel: '取消',
          fromLabel: 'From',
          toLabel: 'To',
          customRangeLabel: '自定义时间段',
          daysOfWeek: ['日', '一', '二', '三', '四', '五', '六'],
          monthNames: ['一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一月', '十二月'],
          firstDay: 1
        }
      };

      dataPicker.daterangepicker(optionSet1, cb);

      dataPicker.on('apply.daterangepicker', function (ev, picker) {
        ajaxFunction(parentId, picker);
      });
      dataPicker.on('cancel.daterangepicker', function () {
        console.log("取消！");
      });

    }

    function ajaxFunction(parentId, picker) {
      console.log("您选中的时间段是： "
        + picker.startDate.format('YYYY-MM-D')//YYYY/MM/D
        + " to "
        + picker.endDate.format('MMMM D, YYYY')
      );

      var start = picker.startDate.format('YYYY-MM-D');
      var end = picker.endDate.format('YYYY-MM-D');
      $.ajax({
        type: "GET",
        //url: "json/weeklydata.json",
        url: "json/hoursdata.json",
        // url: "json/minutedata.json",
        dataType: "json",
        data: "start_date=" + start + "&end_date=" + end,
        success: function (data) {
          renderLineGraph(parentId, $.extend(true, [], data.rows), $.extend(true, [], originAttrs), setting);
        }
      });
    }

  }//end renderLineGraph


  function renderCompareGraph(divId, rows, type, option) {
    var originSeriesDatas = [];
    var originLegendDatas = [];
    var zeroTag = false;//去零标志
    var newSeriesDatas = [];
    var newLegendDatas = [];
    type = type || 'number';

    /* 对排序增加一个标志变量 */
    var sortTag = 'No';

    for (var i = 0; i < rows.length; i++) {
      originLegendDatas[originLegendDatas.length] = rows[i][0];
      var eachdata = {};
      eachdata.name = rows[i][0];
      eachdata.value = rows[i][1];
      originSeriesDatas.push(eachdata);
      if (rows[i][1] !== 0) {
        newSeriesDatas.push(eachdata);
        newLegendDatas.push(eachdata);
      }
    }

    $("#" + divId).empty();
    $("#" + divId).addClass('graphic');
    barGraphic(divId, $.extend(true, [], originLegendDatas), $.extend(true, [], originSeriesDatas), type, zeroTag);

    function pieGraphic(divId, pieLegendDatas, pieSeriesDatas, type, zeroTag) {//divId，图例的label，饼图数据
      var myChart = echarts.init(document.getElementById(divId));
      myChart.setOption({
        tooltip: {
          trigger: 'item',
          formatter: function (params) {
            var tipText = params[1] + "：" + formatYAxis[type](params[2]) + " ( " + params[3] + "% )";
            return tipText;
          }
        },
        legend: {
          orient: 'vertical',
          x: 'left',
          data: pieLegendDatas
        },
        toolbox: {
          show: true,
          feature: {
            barTool: {
              show: true,
              title: '柱状图',
              icon: 'image://data:image/png;base64,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',
              onclick: function () {
                barGraphic(divId, pieLegendDatas, pieSeriesDatas, type, zeroTag);
              }
            },
            zeroTool: {
              show: true,
              title: '去零',
              icon: 'image://data:image/png;base64,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',
              onclick: function () {
                zeroTag = !zeroTag;
                if (zeroTag !== false) {
                  pieGraphic(divId, newLegendDatas, newSeriesDatas, type, zeroTag);
                }
                else{
                  pieGraphic(divId, originLegendDatas, originSeriesDatas, type, zeroTag);
                }
              }
            },
            saveAsImage: {
              show: true,
              title: '保存为图片',
              type: 'jpeg',
              lang: ['点击本地保存']
            }
          }
        },
        calculable: true,
        series: [
          {
            type: 'pie',
            radius: '55%',
            center: ['55%', '60%'],
            data: pieSeriesDatas
          }
        ]
      });
    }

    function barGraphic(divId, barLegendDatas, barSeriesDatas, type, zeroTag) {//divId，x轴的label，相对应的y轴数据
      var myChart = echarts.init(document.getElementById(divId), 'dark');
      myChart.setOption({
        title: {
          text: option.title,
          x: 'center',
          subtext: option.subTitle
        },
        tooltip: {
          trigger: 'axis',
          formatter: function (params) {
            var tipText = params[0][1] + "：" + formatYAxis[type](params[0][2]);
            return tipText;
          }
        },
        toolbox: {
          show: true,
          feature: {
            pieTool: {
              show: true,
              title: '饼图',
              icon: 'image://data:image/png;base64,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',
              onclick: function () {
                pieGraphic(divId, barLegendDatas, barSeriesDatas, type, zeroTag);
              }
            },
            zeroTool: {
              show: true,
              title: '去零',
              icon: 'image://data:image/png;base64,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',
              onclick: function () {
                zeroTag = !zeroTag;
                if (zeroTag !== false) {
                  barGraphic(divId, newLegendDatas, newSeriesDatas, type, zeroTag);
                }
                else{
                  barGraphic(divId, originLegendDatas, originSeriesDatas, type, zeroTag);
                }
              }
            },
            sortTool: {
              show: true,
              title: '升序或降序',
              icon: 'image://data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABkAAAAaCAYAAABCfffNAAAABGdBTUEAALGOfPtRkwAAACBjSFJNAACHDwAAjA8AAP1SAACBQAAAfXkAAOmLAAA85QAAGcxzPIV3AAAKOWlDQ1BQaG90b3Nob3AgSUNDIHByb2ZpbGUAAEjHnZZ3VFTXFofPvXd6oc0w0hl6ky4wgPQuIB0EURhmBhjKAMMMTWyIqEBEEREBRZCggAGjoUisiGIhKKhgD0gQUGIwiqioZEbWSnx5ee/l5ffHvd/aZ+9z99l7n7UuACRPHy4vBZYCIJkn4Ad6ONNXhUfQsf0ABniAAaYAMFnpqb5B7sFAJC83F3q6yAn8i94MAUj8vmXo6U+ng/9P0qxUvgAAyF/E5mxOOkvE+SJOyhSkiu0zIqbGJIoZRomZL0pQxHJijlvkpZ99FtlRzOxkHlvE4pxT2clsMfeIeHuGkCNixEfEBRlcTqaIb4tYM0mYzBXxW3FsMoeZDgCKJLYLOKx4EZuImMQPDnQR8XIAcKS4LzjmCxZwsgTiQ7mkpGbzuXHxArouS49uam3NoHtyMpM4AoGhP5OVyOSz6S4pyalMXjYAi2f+LBlxbemiIluaWltaGpoZmX5RqP+6+Dcl7u0ivQr43DOI1veH7a/8UuoAYMyKarPrD1vMfgA6tgIgd/8Pm+YhACRFfWu/8cV5aOJ5iRcIUm2MjTMzM424HJaRuKC/6386/A198T0j8Xa/l4fuyollCpMEdHHdWClJKUI+PT2VyeLQDf88xP848K/zWBrIieXwOTxRRKhoyri8OFG7eWyugJvCo3N5/6mJ/zDsT1qca5Eo9Z8ANcoISN2gAuTnPoCiEAESeVDc9d/75oMPBeKbF6Y6sTj3nwX9+65wifiRzo37HOcSGExnCfkZi2viawnQgAAkARXIAxWgAXSBITADVsAWOAI3sAL4gWAQDtYCFogHyYAPMkEu2AwKQBHYBfaCSlAD6kEjaAEnQAc4DS6Ay+A6uAnugAdgBIyD52AGvAHzEARhITJEgeQhVUgLMoDMIAZkD7lBPlAgFA5FQ3EQDxJCudAWqAgqhSqhWqgR+hY6BV2ArkID0D1oFJqCfoXewwhMgqmwMqwNG8MM2An2hoPhNXAcnAbnwPnwTrgCroOPwe3wBfg6fAcegZ/DswhAiAgNUUMMEQbigvghEUgswkc2IIVIOVKHtCBdSC9yCxlBppF3KAyKgqKjDFG2KE9UCIqFSkNtQBWjKlFHUe2oHtQt1ChqBvUJTUYroQ3QNmgv9Cp0HDoTXYAuRzeg29CX0HfQ4+g3GAyGhtHBWGE8MeGYBMw6TDHmAKYVcx4zgBnDzGKxWHmsAdYO64dlYgXYAux+7DHsOewgdhz7FkfEqeLMcO64CBwPl4crxzXhzuIGcRO4ebwUXgtvg/fDs/HZ+BJ8Pb4LfwM/jp8nSBN0CHaEYEICYTOhgtBCuER4SHhFJBLVidbEACKXuIlYQTxOvEIcJb4jyZD0SS6kSJKQtJN0hHSedI/0ikwma5MdyRFkAXknuZF8kfyY/FaCImEk4SXBltgoUSXRLjEo8UISL6kl6SS5VjJHslzypOQNyWkpvJS2lIsUU2qDVJXUKalhqVlpirSptJ90snSxdJP0VelJGayMtoybDFsmX+awzEWZMQpC0aC4UFiULZR6yiXKOBVD1aF6UROoRdRvqP3UGVkZ2WWyobJZslWyZ2RHaAhNm+ZFS6KV0E7QhmjvlygvcVrCWbJjScuSwSVzcopyjnIcuUK5Vrk7cu/l6fJu8onyu+U75B8poBT0FQIUMhUOKlxSmFakKtoqshQLFU8o3leClfSVApXWKR1W6lOaVVZR9lBOVd6vfFF5WoWm4qiSoFKmclZlSpWiaq/KVS1TPaf6jC5Ld6In0SvoPfQZNSU1TzWhWq1av9q8uo56iHqeeqv6Iw2CBkMjVqNMo1tjRlNV01czV7NZ874WXouhFa+1T6tXa05bRztMe5t2h/akjpyOl06OTrPOQ12yroNumm6d7m09jB5DL1HvgN5NfVjfQj9ev0r/hgFsYGnANThgMLAUvdR6KW9p3dJhQ5Khk2GGYbPhqBHNyMcoz6jD6IWxpnGE8W7jXuNPJhYmSSb1Jg9MZUxXmOaZdpn+aqZvxjKrMrttTjZ3N99o3mn+cpnBMs6yg8vuWlAsfC22WXRbfLS0suRbtlhOWWlaRVtVWw0zqAx/RjHjijXa2tl6o/Vp63c2ljYCmxM2v9ga2ibaNtlOLtdZzllev3zMTt2OaVdrN2JPt4+2P2Q/4qDmwHSoc3jiqOHIdmxwnHDSc0pwOub0wtnEme/c5jznYuOy3uW8K+Lq4Vro2u8m4xbiVun22F3dPc692X3Gw8Jjncd5T7Snt+duz2EvZS+WV6PXzAqrFetX9HiTvIO8K72f+Oj78H26fGHfFb57fB+u1FrJW9nhB/y8/Pb4PfLX8U/z/z4AE+AfUBXwNNA0MDewN4gSFBXUFPQm2Dm4JPhBiG6IMKQ7VDI0MrQxdC7MNaw0bGSV8ar1q66HK4RzwzsjsBGhEQ0Rs6vdVu9dPR5pEVkQObRGZ03WmqtrFdYmrT0TJRnFjDoZjY4Oi26K/sD0Y9YxZ2O8YqpjZlgurH2s52xHdhl7imPHKeVMxNrFlsZOxtnF7YmbineIL4+f5rpwK7kvEzwTahLmEv0SjyQuJIUltSbjkqOTT/FkeIm8nhSVlKyUgVSD1ILUkTSbtL1pM3xvfkM6lL4mvVNAFf1M9Ql1hVuFoxn2GVUZbzNDM09mSWfxsvqy9bN3ZE/kuOd8vQ61jrWuO1ctd3Pu6Hqn9bUboA0xG7o3amzM3zi+yWPT0c2EzYmbf8gzySvNe70lbEtXvnL+pvyxrR5bmwskCvgFw9tst9VsR23nbu/fYb5j/45PhezCa0UmReVFH4pZxde+Mv2q4quFnbE7+0ssSw7uwuzi7Rra7bD7aKl0aU7p2B7fPe1l9LLCstd7o/ZeLV9WXrOPsE+4b6TCp6Jzv+b+Xfs/VMZX3qlyrmqtVqreUT13gH1g8KDjwZYa5ZqimveHuIfu1nrUttdp15UfxhzOOPy0PrS+92vG140NCg1FDR+P8I6MHA082tNo1djYpNRU0gw3C5unjkUeu/mN6zedLYYtta201qLj4Ljw+LNvo78dOuF9ovsk42TLd1rfVbdR2grbofbs9pmO+I6RzvDOgVMrTnV32Xa1fW/0/ZHTaqerzsieKTlLOJt/duFczrnZ86nnpy/EXRjrjup+cHHVxds9AT39l7wvXbnsfvlir1PvuSt2V05ftbl66hrjWsd1y+vtfRZ9bT9Y/NDWb9nffsPqRudN65tdA8sHzg46DF645Xrr8m2v29fvrLwzMBQydHc4cnjkLvvu5L2key/vZ9yff7DpIfph4SOpR+WPlR7X/aj3Y+uI5ciZUdfRvidBTx6Mscae/5T+04fx/Kfkp+UTqhONk2aTp6fcp24+W/1s/Hnq8/npgp+lf65+ofviu18cf+mbWTUz/pL/cuHX4lfyr468Xva6e9Z/9vGb5Dfzc4Vv5d8efcd41/s+7P3EfOYH7IeKj3ofuz55f3q4kLyw8Bv3hPP74uYdwgAAAAlwSFlzAAAOxAAADsQBlSsOGwAAApBJREFUSEvtls1rE0EYxp9s0mySNqZpabHGirZ+oAVNTC8e6sWDJ09F8Sj0ongUa9WD4EGo4gfxInjoPyAIerDgVcSDtiEVRUHRfqTV2qbtJs1ms8n6zu5svkzzseBB8Lcsyb6zM8/MzrzPjE0jUMLXRAYDjz9CTqk4NeDHszP9vKQ6j6aWceHpN8DtANQ8jgbceDdyiJcaCPxXJ7qUQv+tachKHhDteD6zikBkhpdapyDyZiGF0F1qsN1JUZsRpN7FVzLofhAzni2ii7yalXDsPhewcQETGtFyQkHHPetCwtRiCkOR94C/ioAJCSU2FGy7E+WBIja66iGEJz7TCMStBUycdkhrWVycnOMBA1nN8X9bI0Chl+p3xsBhw4KU5Q8GukidDgqXhrYDqxkgSZXZnStb0UCGGmFx1vimiocnd/KCxtHzZG5Nxq+0im6PA4P0+ZYkFbBT70jg5okenKV8WZdzGAx4ebUi46/jGJuMAy577TzpbXch1NOGgM+FFnP5MvIa+vwi9nV6qgo0SlkyMjS6SslWfj4L/CHyN/gv0hT/hkjZkieEKtlvUUTD27iELytpzJJxFlohgc1sHiy5pxeT+CGRk7Bw5c7YG4lhfp1nPLnAxPBunAt28VIg9jONI+PkxuTMOk5SIPMswPKK6umQS9w+3df8SM6/IBf2tgBt/C4VYLDOmWWdIkZfzjcvsoNVbtQFaBf3kh82LfJkeA+ZIVWjb18T8j3QfEVHDlibeO16GHY2F+zAUQ0u8GH0MBmsy5oIQ70aguhmQhU7Ixf4NBbEwS6PHrIswpCvhNDaSucttrEx2FxJCr5fC2J/h8uIEXVFWMdqkbwcxPG9Pn1EPg+dbG6EsYv2pyLAb3z44lKs4IShAAAAAElFTkSuQmCC',
              onclick: function () {
                //将数据排序后画图
                var barLegendDatas = [];


                function sortDict(objs) {
                  var tuples = [];
                  var barLegendDatas = [];

                  for (var key in objs) {
                    var obj = {};
                    obj.name = objs[key].name;
                    obj.value = objs[key].value;
                    tuples.push([key, obj]);
                  }

                  tuples.sort(function (a, b) {
                    a = a[1].value;
                    b = b[1].value;
                    return a < b ? -1 : (a > b ? 1 : 0);
                  });

                  for(var i=0;i<tuples.length;i++) {
                    barLegendDatas.push(tuples[i][1]);
                  }
                  return barLegendDatas;
                }

                function getLegends(newSeriesDatas){
                  var legends = [];
                  for(var key in newSeriesDatas)
                  {
                    legends.push(newSeriesDatas[key].name);
                  }
                  return legends;
                }

                barLegendDatas = sortDict(newSeriesDatas);
                if (sortTag === 'No') {
                  sortTag = 'DESC';

                  var legends = getLegends(barLegendDatas);
                  barGraphic(divId, legends, barLegendDatas, type, zeroTag);


                }else if(sortTag === 'DESC'){
                  sortTag = 'ASC';

                  var legends = getLegends(barLegendDatas);
                  barGraphic(divId, legends.reverse(), barLegendDatas.reverse(), type, zeroTag);
                }
                else{
                  sortTag = 'No';
                  var legends = getLegends(newSeriesDatas);
                  barGraphic(divId, legends, newSeriesDatas, type, zeroTag);

                }

              }
            },
            saveAsImage: {
              show: true,
              title: '保存为图片',
              type: 'jpeg',
              lang: ['点击本地保存']
            }
          }
        },
        calculable: true,
      dataZoom :  getBarDataZoom(divId, barLegendDatas),
        xAxis: [
          {
            axisLabel:{
              show:true,
              rotate: -45,
              interval:0
            },
            type: 'category',
            axisLine: false,
            data: barLegendDatas
          }
        ],
        yAxis: [
          {
            boundaryGap:[0, 0.05],
            type: 'value',
            axisLine: false,
            axisLabel: {
              formatter: function (v) {
                return numberFormat(v);
              }
            }
          }
        ],
        series: [
          {
            type: 'bar',
            data: barSeriesDatas
          }
        ]
      });
    }

    function getBarDataZoom(divId, barLegendDatas){
      var barDataZoom = {};
      var show = false;
      if((document.getElementById(divId).offsetWidth-100)/barLegendDatas.length < 40){
        show = true;
        barDataZoom.realtime = true;
        barDataZoom.y = 36;
        barDataZoom.start = 40;
        barDataZoom.end = 60;
      }
      barDataZoom.show = show;
      return barDataZoom;
    }

  }//end renderCompareGraph


  function renderGeoGraph(divId, rows, setting) {

    var defaultSetting = {
      title: '',
      subTitle: '', // 可选
      color: '',
      showDataRange: true, // 默认显示
      type: 'number'
    };

    var option = $.extend(true, defaultSetting, setting);

    var geoSeriesDatas = [];
    var geoData = [];

    for (var i = 0; i < rows.length; i++) {
      var eachdata = {};
      eachdata.name = rows[i][0];
      eachdata.value = rows[i][1];
      geoData.push(rows[i][1]);
      geoSeriesDatas.push(eachdata);
    }

    if (option.showDataRange === true) {
      //获取max和mix
      var geoMax = Math.max.apply(null, geoData);
      var geoMin = Math.min.apply(null, geoData);
      geoMax *= 1.05;
      geoMin *= 0.95;
      if ((option.type === 'percent') && (geoMax > 100)) {
        geoMax = 100;
      }
      option.max = geoMax;
      option.min = geoMin;
    }

    //开始画图
    $('#' + divId).empty();
    $('#' + divId).addClass('graphic');
    geoGraphic(divId, $.extend(true, [], geoSeriesDatas), option);

    function geoGraphic(divId, geoSeriesDatas, option) {//divId，图例的label，饼图数据
      var myChart = echarts.init(document.getElementById(divId));
      var geoChartOption = {
        title: {
          text: option.title,
          subtext: option.subTitle,
          x: 'center'
        },
        tooltip: {
          trigger: 'item',
          formatter: function (params) {
            var tipText = params[0] + '<br/>' + params[1] + "：" + formatYAxis[option.type](params[2]);
            return tipText;
          }
        },
        toolbox: {
          show: true,
          feature: {
            saveAsImage: {
              show: true,
              title: '保存为图片',
              type: 'jpeg',
              lang: ['点击本地保存']
            }
          }
        },
        series: getGeoSeries(divId, geoSeriesDatas, option)
      };

      if (option.showDataRange === true) {
        var dataRange = {};
        dataRange.min = option.min;
        dataRange.max = option.max;
        dataRange.text = ['高', '低'];
        dataRange.calculable = true;
        dataRange.color = getRGBColor($.extend(true, [], option.color));
        geoChartOption.dataRange = dataRange;
      }
      myChart.setOption(geoChartOption);

    }//end geoGraphic()

    function getGeoSeries(divId, geoSeriesDatas, option) {

      var geoSeries = [];
      var geoSeriesItem =
      {
        name: option['title'],
        type: 'map',
        mapType: 'china',
        data: geoSeriesDatas
      };
      var itemStyleItem = {};
      var normalItem = {};
      var emphasisItem = {};
      var labelItem = getGeoLabel(divId);
      normalItem.label = labelItem;
      emphasisItem.label = labelItem;
      itemStyleItem.normal = normalItem;
      itemStyleItem.emphasis = emphasisItem;
      geoSeriesItem.itemStyle = itemStyleItem;

      geoSeries.push(geoSeriesItem);
      return geoSeries;
    }

    function getGeoLabel(divId) {
      var labelItem = {};
      var geoContainer = document.getElementById(divId);
      if (geoContainer.offsetWidth < 500 || geoContainer.offsetHeight < 400) {
        labelItem.show = false;
      }
      else if (geoContainer.offsetWidth < 800 || geoContainer.offsetHeight < 700) {
        labelItem.show = true;
      }
      else if (geoContainer.offsetWidth < 1000 || geoContainer.offsetHeight < 900) {
        labelItem.show = true;
        var textStyleItem = {};
        textStyleItem.fontSize = 15;
        labelItem.textStyle = textStyleItem;
      }
      else {
        labelItem.show = true;
        var textStyleItem = {};
        textStyleItem.fontSize = 17;
        labelItem.textStyle = textStyleItem;
      }
      return labelItem;
    }

    function getRGBColor(color) {
      for (var i = 0; i < color.length; i++) {
        if (color[i].indexOf('rgba') > -1) {
          color[i] = rgbaToRgb(color[i]);
        }
      }
      return color;
    }

    function rgbaToRgb(source) {
      var startIndex = source.indexOf('(') + 1;
      var endIndex = source.indexOf(')');
      var sourceNum = (source.slice(startIndex, endIndex)).split(',');

      var r = parseInt(sourceNum[0]);
      var g = parseInt(sourceNum[1]);
      var b = parseInt(sourceNum[2]);
      var a = parseFloat(sourceNum[3]);

      var rResult = Math.round(((1 - a) * 255) + (a * r));
      var gResult = Math.round(((1 - a) * 255) + (a * g));
      var bResult = Math.round(((1 - a) * 255) + (a * b));

      return "rgb(" + rResult + "," + gResult + "," + bResult + ")";
    }

  }//end renderGeoGraph()

  /*
   * steps = [[0, label], [100, label]]
   */
  var stepFormatter = function(steps){
    steps.sort(function(row1, row2){ return row2[0] - row1[0]; });

    return function(v){
      var len = steps.length;
      for (var i=0; i<len; i++) {
        var row = steps[i];

        if ( v > row[0] ) {
          return (v / row[0]).toFixed(2) + row[1];
        }
      }

      return v;
    };
  };

  var formatYAxis = {//支持的Y轴类型，不支持时，转为number型
    'series': function (v) {
      return v;
    },
    'number': function (v) {
      return numberFormat(v);
    },
    'time': function (v) {
      return timeFormat(v);
    },
    'percent': function (v) {
      return percentFormat(v);
    },
    size: stepFormatter([
      [1024, 'K'], [1024 * 1024, 'M'], [1024 * 1024 * 1024, 'G'],
      [Math.pow(1024, 4), 'T'], [Math.pow(1024, 5), 'P'],
    ]),
    'speed': function (v) {
      return speedFormat(v);
    }
  };

  function timeFormat(v) {
    if (v > 3600) {
      return ((v / 3600).toFixed(2) + ' h');
    }
    else if (v > 300) {
      return ((v / 60).toFixed(2) + ' min');
    }
    else if (v < 0.01) {
      return ((v * 1000).toFixed(2) + ' ms');
    }
    else {
      return v + ' s';
    }
  }

  function percentFormat(v) {
    if (v < 0.1) {
      return ((v * 10).toFixed(2) + ' ‰');
    }
    else {
      return v + ' %';
    }
  }

  var sizeFormat = stepFormatter([
    [1024, 'K'],
    [1024 * 1024, 'M'],
    [1024 * 1024 * 1024, 'G'],
    [Math.pow(1024, 4), 'T'],
    [Math.pow(1024, 5), 'P'],
  ]);

  var numberFormat = stepFormatter([
    [10000, '万'],
    [Math.pow(10000, 2), '亿'],
    [Math.pow(10000, 3), '万亿'],
  ]);

  function speedFormat(v) {
    if (v > 1000) {
      return ((v / 1000).toFixed(2) + ' Mb/s');
    }
    else if (v < 0.01) {
      return ((v * 1000).toFixed(2) + ' b/s');
    }
    else {
      return  v + " kb/s";
    }
  }

  exports.renderGeoGraph = renderGeoGraph;
  exports.renderCompareGraph = renderCompareGraph;
  exports.renderLineGraph = renderLineGraph;

  exports.formatter = {
    number: numberFormat,
    speed: speedFormat,
    size: sizeFormat,
    percent: percentFormat,
    time: timeFormat
  };

  exports.regroupSeries = function(rows) {
    var len = rows.length;
    var columns = rows[0].length - 1;
    var groups = [];

    for (var j=0; j<columns; j++) {
      groups.push([]);
    }

    for (var i = 0; i < len; i++) {
      var row = rows[i];

      for (var m=0; m < columns; m ++ ) {
        groups[m].push([row[0], row[m+1]]);
      }
    }

    return groups;
  };

})(window, window.jQuery, window.echarts, window.moment);
