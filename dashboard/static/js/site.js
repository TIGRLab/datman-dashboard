$("#find_session").bind('click', function(){
  var search_text = $("#find_session_text").val();
  if(search_text){
    var root = location.protocol + '//' + location.host + '/';
    var url = root + 'session_by_name' + '/' + search_text;
    window.location.href=url;
  }
  return false;
});

$(".btn_view_scan_comments").on('click', function(){
  var scan_id = $(this).closest('tr').attr('id').split('_')[1];
  $('#scan_comments_' + scan_id).toggle();
})

$(".btn_add_scan_comments").on('click', function(){
  var el_row = $(this).closest('tr')
  var scan_id = el_row.attr('id').split('_')[1];

  var el_title = $("#add_scan_comment_modal .modal-title");

  /* set the form target */
  var root = location.protocol + '//' + location.host + '/';
  var target_uri = root + 'scan_comment/' + scan_id;

  var scan_name = el_row.find('.scan_desc').text();
  var scan_name = el_title.html() + ' - ' + scan_name;

  $("#add_scan_comment_modal #scan_id").val(scan_id);
  $("#add_scan_comment_modal .modal-title").html(scan_name);
  $("#add_scan_comment_modal .form").attr('action', target_uri);
})
