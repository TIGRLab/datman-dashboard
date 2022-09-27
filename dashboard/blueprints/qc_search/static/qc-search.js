/* Functions to implement the QC search form and display */

$('#qc-search-form').submit(function(e) {
  e.preventDefault();

  function failFunc(response) {
    console.log("Failed to handle request");
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
    data: $(this).serialize(),
    success: function() {console.log("Success!");},
    error: failFunc
  });

});
