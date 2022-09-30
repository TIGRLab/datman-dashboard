/* Functions to implement the QC search form and display */

function parseValue(value) {
  /* Convert 'nulls' to empty strings and perform any other formatting needed
     for table values
  */
  if (value === null) {
    return ""
  }

  return value
}

function displayRecords(records) {
  var tableBody = $("#qc-search-results-table tbody")[0];

  let body = "";
  for (let i = 0; i < records.length; i += 1) {
    body += `
      <tr>
        <td>${records[i]['name']}</td>
        <td>${parseValue(records[i]['approved'])}</td>
        <td>${parseValue(records[i]['comment'])}</td>
      </tr>
    `
  }

  tableBody.innerHTML = body;
};

function makeCsv() {
  /* Construct a csv from the currently displayed search records */
  var csv = [];
  var rows = $("#qc-search-results-table tr");
  for (var i = 0; i < rows.length; i += 1) {
    var cols = rows[i].querySelectorAll('td,th');
    var col = []
    for (var j = 0; j < cols.length; j += 1) {
      col.push(cols[j].innerHTML);
    }
    csv.push(col.join(","));
  }
  return csv.join("\n");
};

function downloadCsv() {
  /* Download the search results as a csv */
  var downloadBtn = $("#qc-download")[0];
  var outFile = new Blob([makeCsv()], {type: "text/csv"});
  var url = window.URL.createObjectURL(outFile);
  downloadBtn.href = url;
};

$("#qc-download").on("click", downloadCsv);

$("#qc-search-form").submit(function(e) {
  /* Submit the search terms to the server and handle response. */
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
    success: displayRecords,
    error: failFunc
  });

});

$("#qc-search-reset").on("click", function() {
  // Reset the form when the 'clear' button is clicked
  $("#qc-search-form")[0].reset();
});
