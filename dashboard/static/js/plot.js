function get_src(d, element){
  session_id = overallSubjectList[d.name][d.index]
  window.location.href = '/session/' + session_id
}

/**
 * Simple function to generate an array of numbers from 0 to length - 1
 */
function gen_range(length){
  return Array.apply(null, Array(length)).map(function (_, i) {return i;});

}

/**
 * initPlot takes an HTML element and list of objects and draws a metric plot using c3 and d3.
 * 
 */
function initPlot(element, data){

//Check if database query was successful.
var dataList = data;
if (typeof(dataList) == "undefined") {
  return;
}

//Sets to keep track of unique sites and scantypes.
var siteSet = new Set();
var site_scantype_set = new Set();

//Lists for metrics, subjects, session names.
var valueList = [];
var subjectList = [];
var sessionNameList = [];

//List of lists (to hold metrics for each site separately).
var overallValueList = [];
session_lengths = []
overallSubjectList = {};
overallSessionNameList = {};

//Generate set of unique sites and scantypes.
dataList.forEach(function(entry){
  siteSet.add(entry.site_name);
  site_scantype_set.add(entry.site_name + ':' + entry.scan_description);
});

//For each scantype/site combination,
site_scantype_set.forEach(function(site_scantype){
  valueList = [];
  subjectList = [];
  sessionNameList = [];
  dataList.forEach(function(entry){
    entry_site_scantype = entry.site_name + ':' + entry.scan_description;
    //add metric value (and subject/session names) to list if it matches combination.
    if (entry_site_scantype == site_scantype) {
      valueList.push(entry.value);
      subjectList.push(entry.session_id);
      sessionNameList.push(entry.session_name);
    }
  } );
  //"Unshift" is prepending to a list.
  valueList.unshift(site_scantype);
  overallValueList.push(valueList);
  session_lengths.push(subjectList.length);
  overallSubjectList[site_scantype] = subjectList;
  overallSessionNameList[site_scantype] = sessionNameList;
});

var max_session_length = Math.max.apply(null, session_lengths);

//Draw chart.
var chart = c3.generate({
    bindto: element,
    data: {
        columns: overallValueList,
        onclick: get_src

    },
    axis: {
      x: {
        type: 'category',
        show: true,
        categories: gen_range(max_session_length), //TODO
        label: 'Time',
        tick: {
          values: []
        }
      }
    },
    //Settings to customize tooptip (shown when hovering datapoint).
    tooltip: {
    grouped: false,
    contents: function(d, defaultTitleFormat, defaultValueFormat, color) {
      console.log(d[0]);
      session_name = overallSessionNameList[d[0].name][d[0].index];
      session_value = Math.round((d[0].value + 0.00001) * 100) / 100
      text = "<table class='c3-tooltip'> <tr><th colspan='2'>" + session_name + "</th></tr>";
      text = text + "<tr><td>Value:</td><td class='c3-value'>" + session_value + "</td></tr>"
      return text + "</table>";
    }
},
//Allow rescaling of x axis.
zoom: {
    enabled: true
}
});
}
