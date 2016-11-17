function getQueryParams(element){
  // queries the selected elements on the page to get the query parameters
  // returns false if not all parameters are selected
  var study = ''
  var siteSet = []
  var scanType = ''
  var metricType = ''
  var phantom = ''
  study = element.find("#study_name").text()
  phantom = element.find("#phantoms").text()

  $.each(element.find("input[name='site']:checked"), function(){
    siteSet.push($(this).val());
  });
  scanType = element.find("input[name='scantype']:checked").val();
  metricType = element.find("#metrictypeselector").find('[data-bind="label"]').text();
  if (metricType.trim() == "Metric Type:"){
    metricType = false;
  }

  if(study && phantom && siteSet.length > 0 && scanType && metricType){
    return { studies:study,
             sites:siteSet.join(','),
             scantypes:scanType,
             metrictypes:metricType,
             isphantom:phantom,
             byname:'1'
           };
  } else {
    return false;
  }
}

function updatePlot(){
  var base_element = $(this).closest('.metrics')
  var params = getQueryParams(base_element)
  var base_url = "/metricDataAsJson"
  if(params){
    base_element.find('#loading_chart').show()

    $.getJSON( base_url, params,
      function ( data ) {
        base_element.find('#loading_chart').hide()
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

// make the sessions table dynamic
$(document).ready(function (){
  $('#tbl_sessions').DataTable();
})
