function get_src(d, element){
  session_id = overallSubjectList[d.name][d.index]
  window.location.href = '/session/' + session_id
}

function gen_range(length){
  // simple function to generate an array of numbers from 0 to length - 1
  return Array.apply(null, Array(length)).map(function (_, i) {return i;});

}

function initPlot(element, data){

//var dataFromSelection = document.getElementById('data');
//var dataList = JSON.parse(dataFromSelection.innerHTML);
var dataList = data
var siteSet = new Set();
var valueList = [];
var subjectList = [];
var overallValueList = [];
session_lengths = []
overallSubjectList = {};

dataList.forEach(function(entry){
  siteSet.add(entry.site_name);
});

siteSet.forEach(function(site){
  valueList = [];
  subjectList = [];
  dataList.forEach(function(entry){
    if (entry.site_name == site) {
      valueList.push(entry.value);
      subjectList.push(entry.session_id);
    }
  } );
  valueList.unshift(site);
  overallValueList.push(valueList);
  session_lengths.push(subjectList.length);
  overallSubjectList[site] = subjectList;
});

var max_session_length = Math.max.apply(null, session_lengths);

var chart = c3.generate({
    bindto: element,
    data: {
        columns: overallValueList,
        onclick: get_src

    },
    axis: {
      x: {
        type: 'category',
        show: false,
        categories: gen_range(max_session_length) //TODO
      }
    },
    tooltip: {
    grouped: false
},
zoom: {
    enabled: true
}
});
}
