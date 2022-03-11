function addLoading(scanId) {
  /* Add a loading indicator in place of the 'qc bar' */
  var barId = '#qc-bar-' + scanId;
  $('<div id="gear-' + scanId + '">' +
    '<span class="fa-4x"><i class="fas fa-cog fa-spin"></i></span> Working' +
    '</div>'
  ).insertAfter(barId);
  $(barId).hide();
}


function delLoading(scanId) {
  /* Remove a loading indicator from a 'qc bar' */
  $('#gear-' + scanId).remove();
  $('#qc-bar-' + scanId).show();
}


function reviewScan(scanData, success_func, error_func) {
  /* Add a new QC review to a scan without reloading the page */

  // csrfToken and reviewScanUrl must be defined by Jinja in the html template
  $('#qc-fail-' + scanData['scan']).remove();

  $.ajaxSetup({
      beforeSend: function(xhr, settings) {
          if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) &&
              !this.crossDomain) {
              xhr.setRequestHeader('X-CSRFToken', csrfToken)
          }
      }
  })

  $.ajax({
    type: 'POST',
    url: reviewScanUrl,
    contentType: 'application/json',
    dataType: 'json',
    data: JSON.stringify(scanData),
    success: success_func,
    error: error_func,
  });
}


function qcFailFunc(response) {
  /* Handles a failed QC review update */

  var scan = response['scan'];
  delLoading(scan);

  if ($('#qc-fail-' + scan).length !== 0) {
    return
  }

  $('<span id="qc-fail-' + scan + '">Update failed, please contact an ' +
    'admin.</span>').insertAfter(
    '#qc-bar-' + scan
  );
}


function qcSuccessFunc(response, status) {
  /* Handles a successful QC review update */

  var scan = response['scan'];
  var qcSig = '#qc-signature-' + scan;
  $(qcSig).text(response['user'] + ' at ' + response['timestamp']);
  $(status).insertBefore(qcSig);

  delLoading(scan);
  $("#scan-comment").val("");
  $('#qc-btns-' + scan).hide();
  $('#qc-display-' + scan).show();
}


function addQcComment(scan, comment) {
  /* Update the UI to show a new QC comment for a scan */
  var display = "#qc-display-" + scan;
  $(display + ' .qc-scan-comment').text(comment);
  $(display + ' .comment-display').show();
}


function delQcComment(scan) {
  /* Remove a scan's QC comment from the UI */
  var display = "#qc-display-" + scan;
  $(display + ' .qc-scan-comment').text('');
  $(display + ' .comment-display').hide();
}


$('.approve-scan').off().on('click', function() {
  /* Approve a scan and update the UI without reloading the page */
  var scanData = $(this).parent()[0].dataset;
  scanData['approve'] = true;
  addLoading(scanData.scan);

  function successFunc(response) {
    response['scan'] = scanData['scan'];
    var status = '<span id="' + 'qc-status-' + scanData['scan'] +
      '" class="qc-approved"><span class="fas fa-check circle">' +
      '</span> Reviewed</span>';
    qcSuccessFunc(response, status);
  }

  function failFunc(response) {
    response['scan'] = scanData['scan'];
    qcFailFunc(response);
  }

  reviewScan(scanData, successFunc, failFunc);
});


$('.flag-scan').off().on('click', function() {
  /* Flag a scan and update the UI without reloading the page */
  var scanData = $(this).parent()[0].dataset;
  scanData['approve'] = true;

  $('#scan-comment-form').off().on('submit', function(e) {
    e.preventDefault();
    scanData['comment'] = $('#scan-comment').val();
    $('#add-review-modal').modal('hide');
    addLoading(scanData['scan']);

    function successFunc(response) {
      addQcComment(scanData['scan'], scanData['comment']);
      var status = '<span id="qc-status-' + scanData['scan'] +
          '" class="qc-flagged"><span class="fas fa-exclamation-triangle"' +
          '></span> Flagged </span>';
      response['scan'] = scanData['scan'];
      qcSuccessFunc(response, status);
    }

    function failFunc(response) {
      response['scan'] = scanData['scan'];
      qcFailFunc(response);
    }

    reviewScan(scanData, successFunc, failFunc);
  });
});


$('.blacklist-scan').off().on('click', function() {
  /* Blacklist a scan and update the UI without reloading the page */
  var scanData = $(this).parent()[0].dataset;
  scanData['approve'] = false;

  $('#scan-comment-form').off().on('submit', function(e) {
    e.preventDefault();
    scanData['comment'] = $('#scan-comment').val();
    $('#add-review-modal').modal('hide');
    addLoading(scanData['scan']);

    function successFunc(response) {
      addQcComment(scanData['scan'], scanData['comment']);
      var status = '<span id="qc-status-' + scanData['scan'] +
          '" class="qc-blacklisted"><span class="fas fa-ban">' +
          '</span> Blacklisted</span>';
      response['scan'] = scanData['scan'];
      qcSuccessFunc(response, status);
    }

    function failFunc(response) {
      response['scan'] = scanData['scan'];
      qcFailFunc(response);
    }

    reviewScan(scanData, successFunc, failFunc);
  });
});


$('.qc-delete').off().on('click', function() {
  /* Delete an existing QC review without reloading the page */
  var scanData = $(this)[0].dataset;
  scanData['delete'] = true;

  addLoading(scanData['scan']);

  function successFunc() {
    $('#qc-status-' + scanData['scan']).remove();
    $('#qc-display-' + scanData['scan']).hide();
    $('#qc-btns-' + scanData['scan'])[0].removeAttribute('data-comment');
    delQcComment(scanData['scan']);
    delLoading(scanData['scan']);
    $('#qc-btns-' + scanData['scan']).show();
  }

  function failFunc(response) {
    response['scan'] = scanData['scan'];
    qcFailFunc(response);
  }

  reviewScan(scanData, successFunc, failFunc);
});


$('.qc-update').off().on('click', function() {
  /* Update an existing QC review without reloading the page */
  var scanData = $(this)[0].dataset;
  scanData['update'] = true;
  $('#scan-comment').val(
      $('#qc-display-' + scanData['scan'] +
        ' .qc-scan-comment').text().trim()
  );

  $('#scan-comment-form').off().on('submit', function(e) {
    e.preventDefault();
    scanData['comment'] = $('#scan-comment').val();
    $('#add-review-modal').modal('hide');

    function successFunc(response) {
      addQcComment(scanData['scan'], scanData['comment']);
      $('#qc-signature-' + scanData['scan']).text(
          response['user'] + ' at ' + response['timestamp']
      );
    }

    function failFunc(response) {
      response['scan'] = scanData['scan'];
      qcFailFunc(response);
    }

    reviewScan(scanData, successFunc, failFunc);
  });
}

);
