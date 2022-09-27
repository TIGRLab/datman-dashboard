/* Functions to implement the QC search form and display */

$('.qc-search-submit').off().on('click', function(e) {
  e.preventDefault();

  function failFunc(response) {
    console.log(response);
  }

  $.ajaxSetup({
    beforeSend: function(xhr, settings) {
      if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) &&
          !this.crossDomain) {
          xhr.setRequestHeader('X-CSRFToken', csrfToken)
      }
    }
  });

  $.ajax({
    type: 'POST',
    url: searchUrl,
    contentType: 'application/json',
    success: function() {console.log("Success!");},
    error: failFunc
  });
});
