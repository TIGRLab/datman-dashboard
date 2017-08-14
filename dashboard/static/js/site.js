/*
Most clientside javascript functionality is found here.
Most actions are bound to html elements either by thier id (e.g. $("#find_session").bind())
or by their class e.g $(".btn_view_scan_comments").bind()
*/

/*
Function for the seach  for session submit button
*/
$("#find_session").bind('click', function(){
  var search_text = $("#find_session_text").val();
  if(search_text){
    var root = location.protocol + '//' + location.host + '/';
    var url = root + 'session_by_name' + '/' + search_text;
    window.location.href=url;
  }
  return false;
});

/*
Functionality for view scan comments in scan_snip.html
Toggles visibilty for the comment based on the clicked elements id
*/
$(".btn_view_scan_comments").on('click', function(){
  var scan_id = $(this).closest('tr').attr('id').split('_')[1];
  $('#scan_comments_' + scan_id).toggle();
})

/*
Functionality for add scan comments in scan_snip.html
Creates a modal form prepopulated with the scan_id
*/
$(".btn_add_scan_comments").on('click', function(){
  // setup the modal dialog with scan specific info
  var scan_id = $(this).data('scanid');
  var scan_name = $(this).data('scanname');

  // set the form target
  var root = location.protocol + '//' + location.host + '/';
  var target_uri = root + 'scan_comment/' + scan_id;

  var el_title = $("#add_scan_comment_modal .modal-title");
  var scan_name = el_title.html() + ' - ' + scan_name;

  $("#add_scan_comment_modal #scan_id").val(scan_id);
  $("#add_scan_comment_modal .modal-title").html(scan_name);
  $("#add_scan_comment_modal .form").attr('action', target_uri);
})

/*
Functionality for add scan to blacklist comments in scan_snip.html
Creates a modal form prepopulated with the scan_id
*/
$(".btn_add_scan_blacklist").on('click', function(){
  // setup the modal dialog with scan specific info
  var scan_id = $(this).data('scanid');
  var scan_name = $(this).data('scanname');

  // set the form target
  var root = location.protocol + '//' + location.host + '/';
  var target_uri = root + 'scan_blacklist/' + scan_id;

  var el_title = $("#add_scan_comment_modal .modal-title");
  var scan_name = el_title.html() + ' - ' + scan_name;

  $("#add_scan_comment_modal #scan_id").val(scan_id);
  $("#add_scan_comment_modal .modal-title").html(scan_name);
  $("#add_scan_comment_modal .form").attr('action', target_uri);
})
