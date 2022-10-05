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
  let tableBody = $("#qc-search-results-table tbody")[0];

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
  delLoadingStatus();
};

function makeCsv() {
  /* Construct a csv from the currently displayed search records */
  let csv = [];
  let rows = $("#qc-search-results-table tr");
  for (let i = 0; i < rows.length; i += 1) {
    let cols = rows[i].querySelectorAll('td,th');
    let col = []
    for (let j = 0; j < cols.length; j += 1) {
      col.push(cols[j].innerHTML);
    }
    csv.push(col.join(","));
  }
  return csv.join("\n");
};

function downloadCsv() {
  /* Download the search results as a csv */
  let downloadBtn = $("#qc-download")[0];
  let outFile = new Blob([makeCsv()], {type: "text/csv"});
  let url = window.URL.createObjectURL(outFile);
  downloadBtn.href = url;
};

function addLoadingStatus() {
  /* Update the search button text + disable button */
  let btn = $("#qc-search-btn")[0];
  btn.innerHTML = '<span class="fa-lg"><i class="fas fa-cog fa-spin"></i></span> Working';
  btn.disabled = true;
};

function delLoadingStatus() {
  /* Update the search button text + enable button */
  let btn = $("#qc-search-btn")[0];
  btn.innerHTML = '<span class="fas fa-search"></span> Search';
  btn.disabled = false;
}

function failedSearch(response) {
  console.log("Firing off fail function");
  $("#qc-search-terms-display").prepend(
    '<div id="qc-search-fail" class="alert alert-danger" role="alert">' +
    'Failed to search database, please contact an admin.' +
    '<button type="button" class="close" data-dismiss="alert">&times;</button>' +
    '</div>');
  delLoadingStatus();
}

$("#qc-download").on("click", downloadCsv);

$("#qc-search-btn").on("click", function() {
  $("#qc-search-form").submit();
  addLoadingStatus();
});

$("#qc-search-form").submit(function(e) {
  /* Submit the search terms to the server and handle response. */
  e.preventDefault();

  function failFunc(response) {
    console.log("Failed to handle request");
    delLoadingStatus();
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
    error: failedSearch
  });

});

$("#qc-search-reset").on("click", function() {
  // Reset the form when the 'clear' button is clicked
  $("#qc-search-form")[0].reset();
});
