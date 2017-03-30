$("#find_session").bind('click', function(){
  var search_text = $("#find_session_text").val();
  if(search_text){
    var root = location.protocol + '//' + location.host + '/';
    var url = root + 'session_by_name' + '/' + search_text;
    window.location.href=url;
  }
  return false;
});
