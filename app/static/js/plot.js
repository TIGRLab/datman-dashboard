function initPlot(element, data){

//var dataFromSelection = document.getElementById('data');
//var dataList = JSON.parse(dataFromSelection.innerHTML);
var dataList = data
var siteSet = new Set();
var valueList = [];
var subjectList = [];
var overallValueList = [];
var overallSubjectList = [];

dataList.forEach(function(entry){
  siteSet.add(entry.site_name);
});

siteSet.forEach(function(site){
  valueList = [];
  subjectList = [];
  dataList.forEach(function(entry){
    if (entry.site_name == site) {
      valueList.push(entry.value);
      subjectList.push(entry.session_name)
    }
  } );
  valueList.unshift(site);
  overallValueList.push(valueList);
  overallSubjectList.push(subjectList);
});


var chart = c3.generate({
    bindto: element,
    data: {
        columns:
          overallValueList

    },
    axis: {
      x: {
        type: 'category',
        show: false,
        categories: overallSubjectList[0] //TODO
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
