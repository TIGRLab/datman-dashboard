function getQueryParams(element){
  // queries the selected elements on the page to get the query parameters
  // returns false if not all parameters are selected
  var study = ''
  var siteSet = []
  var scantypeSet = []
  var scanType = ''
  var metricType = ''
  var phantom = ''
  study = element.find("#study_name").text()
  phantom = element.find("#phantoms").text()

  $.each(element.find("input[name='site']:checked"), function(){
    if($(this).is(':visible')){
      siteSet.push($(this).val());
    }
  });
  // modification to enable multiple scantypes to be selected
  $.each(element.find("input[name='scantype']:checked"), function(){
    if($(this).is(':visible')){
      scantypeSet.push($(this).val());
    }
  });
  // scanType = element.find("input[name='scantype']:checked").val();
  metricType = element.find("#metrictypeselector").find('[data-bind="label"]').text();
  if (metricType.trim() == "Metric Type:"){
    metricType = false;
  }

  if(study && phantom && siteSet.length > 0 && scantypeSet.length > 0 && metricType){
    return { studies:study,
             sites:siteSet.join(','),
             scantypes:scantypeSet.join(','),
             metrictypes:metricType,
             isphantom:phantom,
             byname:'1'
           };
  } else {
    return false;
  }
}

//In callback function, this[0] is mean, this[1] is stdev, this[2] is number of stdevs to set threshold at
function notOutlier(element){
  return ((element.value <= this[0] + this[1] * this[2]) && (element.value >= this[0] - this[1] * this[2]));
};

//Update plot without outliers (if specified in form).
function noOutliersPlot(){
  var base_element = $(this).closest('.metrics')
  var params = getQueryParams(base_element)
  var base_url = "/metricDataAsJson"
  if(params){
    base_element.find('#loading_chart').show()
    //Parse JSON as list of Javascript objects
    $.getJSON( base_url, params,
      function ( data ) {
        base_element.find('#loading_chart').hide()
        var sum = 0;
        var dat = data['data'];
        var n = dat.length;

        dat.forEach(function(entry){
          sum += entry.value;
        });

        //Calculate mean and STD of metric values.
        var mean = sum / n;
        var sumsqdiff = 0;
        dat.forEach(function(entry){
          sumsqdiff += Math.pow(mean - entry.value, 2);
        });
        std = Math.sqrt(sumsqdiff / n);

        //Number of standard deviations to exclude (make this user selectable)
        var threshold = 2;
        initPlot(base_element.find('#chart')[0], dat.filter(notOutlier, [mean, std, threshold]));
      });
  }
}


//Function bound to clicking form elements (so plot is updated after changing each value).
function updatePlot(){
  var base_element = $(this).closest('.metrics')
  var params = getQueryParams(base_element)
  //Fetch data from database through "metricDataAsJson" view
  var base_url = "/metricDataAsJson"
  if(params){
    base_element.find('#loading_chart').show()
    //Parse JSON as list of Javascript objects
    $.getJSON( base_url, params,
      function ( data ) {
        if (data['data'].length == 0){
          base_element.find('#loading_chart').hide()
          document.getElementById('chart').innerHTML = "No data for these settings. Try a different metric type or scan type."
          return;
        }
        base_element.find('#loading_chart').hide()
        base_element.find('#remove_outliers').show()
        //Draw plot with new data
        initPlot(base_element.find('#chart')[0], data['data']);
      });
  }
}
// event to modify displayed text on dropdown-menu buttons
$( ".dropdown-menu li").bind('click' , function( event ){
  var $target = $( event.currentTarget );
  var $group = $target.closest( '.btn-group' ) //the containing button group
  var newlabel = $target.text().trim()
  var base_element = $(this).closest('.metrics')
  $group
    .find( '[data-bind="label"]').text( newlabel + ' ')
      .end()
    .children ('.dropdown-toggle' ).dropdown( 'toggle' );
  //sub event to update displayed values
  if($group.attr("id") == 'scanclassselector'){
    if (newlabel == 'FMRI'){
      //make all elements with class scantype_fmri visible
      //hide all elements with class scantype_dti
      $(".scantype_dti").hide();
      $(".scantype_fmri").show();
      $(".scantype_t1").hide();
    }else if (newlabel == 'DTI') {
      $(".scantype_dti").show();
      $(".scantype_fmri").hide();
      $(".scantype_t1").hide();
    }else if (newlabel == 'T1'){
      $(".scantype_dti").hide();
      $(".scantype_fmri").hide();
      $(".scantype_t1").show();
    }
    //reset the metrictype selector
    base_element.find("#metrictypeselector")
      .find( '[data-bind="label"]').text( 'Metric Type:')
        .end()
  }
});
// bind the create plot function to the sites, scantypes and metrictypes
$("input[name='site']").bind('click', updatePlot);
$("#metrictypeselector li").bind('click', updatePlot);
$("input[name='scantype']").bind('click', updatePlot);
$("#remove_outliers").bind('click', noOutliersPlot);

// make the sessions table dynamic
$(document).ready(function (){
  $('#tbl_sessions').DataTable();
})
