<script type="text/javascript">
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
  /*
  var el_row = $(this).closest('tr')
  var scan_id = el_row.attr('id').split('_')[1];

  var el_title = $("#add_scan_comment_modal .modal-title");

  var scan_name = el_row.find('.scan_desc').text();
  var scan_name = el_title.html() + ' - ' + scan_name;
  */
  
  // set the form target
  var root = location.protocol + '//' + location.host + '/';
  var target_uri = root + 'scan_comment/' + scan_id;

  // setup the modal dialog with scan specific info
  var scan_id = $(this).data('scanid');
  var scan_name = $(this).data('scanname')

  var el_title = $("#add_scan_comment_modal .modal-title");
  var scan_name = el_title.html() + ' - ' + scan_name;

  $("#add_scan_comment_modal #scan_id").val(scan_id);
  $("#add_scan_comment_modal .modal-title").html(scan_name);
  $("#add_scan_comment_modal .form").attr('action', target_uri);
})

$("#print_brain").bind('click', function(){
  alert('Coming soon!');
});

$('#edit_qc').bind('click', function(){
  $('#qc_comment').collapse('toggle');
  $('#qc_form').collapse('toggle');
})

$('.btn_blacklist').bind('click', function(){
  window.location.href = "{{url_for('scan')}}/" + $(this).attr('value')
})

$('#delete_session').bind('click', function(){
  window.location.href = "{{url_for('session',session_id=session.id, delete=True)}}";
})

$('#goto_issue').bind('click', function(){
  window.location.href = "https://github.com/TIGRLab/admin/issues/{{session.gh_issue}}"
})

$('#create_issue').bind('click', function(){
   /*ECMA6 import syntax that doesn't work on most browsers...probably better to move this to server
  import Issue from "github-api";

  var iss = new Issue("TIGRLab/admin",
    {
      //Removed token
    token: ""
  });
  Issue.createIssue({
    title: issTitle,
    body: issDetails
  });
 */
  var issTitle = prompt("Please enter a title for the issue:", "{{ session.name }}");
  if (issTitle === null) {
    return;
  }

  var issBody = prompt("Please enter issue details:", "");
  if (issBody === null) {
    return;
  }

  url = "{{url_for('create_issue', session_id=session.id)}}/" + encodeURIComponent(issTitle) + '/' + encodeURIComponent(issBody)
  window.location.href = url;
})
</script>
