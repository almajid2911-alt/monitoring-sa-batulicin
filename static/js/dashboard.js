(function () {
  const jamPs = JSON.parse(document.getElementById("jam-ps-data").textContent);
  const jamRe = JSON.parse(document.getElementById("jam-re-data").textContent);

  // ─── Badge Modal Helper ───────────────────────────────────────────────────
  function showBadgeModal(track, status, morning, catatan) {
    $("#badge-modal-tr").text(track);
    $("#badge-modal-status").text(status);
    $("#badge-modal-morning").text(morning);
    $("#badge-modal-catatan").html((catatan || "-").replace(/\n/g, "<br/>"));
    var bm = bootstrap.Modal.getOrCreateInstance(document.getElementById("badgeModal"));
    bm.show();
  }

  // ─── DataTable: rowGroup by WORKZONE, TIM in Column 1 beside order ────
  let dataTable = $("#detailTable").DataTable({
    paging: true,
    pageLength: 50,
    searching: true,
    info: true,
    ordering: true,
    order: [[0, "asc"], [1, "asc"], [3, "asc"]],
    rowGroup: {
      dataSrc: 0,
      startRender: function(rows, group) {
        return $('<tr class="dt-rowgroup-wz"/>').append(
          $('<td colspan="4"/>').html(
            '<i class="bi bi-geo-alt-fill me-2"></i><strong class="text-uppercase" style="font-size:0.82rem;">' + group + '</strong>' +
            '<span class="badge bg-secondary ms-2" style="font-size:0.65rem;">' + rows.count() + ' order</span>'
          )
        );
      }
    },

    columnDefs: [
      { targets: [0], visible: false, searchable: true }
    ],
    scrollX: false,
    language: {
      search: "Cari:",
      lengthMenu: "Tampilkan _MENU_ data",
      info: "Menampilkan _START_ sampai _END_ dari _TOTAL_ data",
      paginate: { previous: "←", next: "→" },
      zeroRecords: "Tidak ada data yang cocok",
      infoEmpty: "Tidak ada data",
      infoFiltered: "(difilter dari _MAX_ total data)",
    },
    rowCallback: function (row, data, displayNum, displayIndex) {
      const api = this.api();
      const currentWz = data[0] || "";
      const currentTimCell = $(row).find("td").eq(0);
      const currentTim = currentTimCell.attr("data-tim") || currentTimCell.text().trim();

      if (displayIndex > 0) {
        const prevRowNode = api.row(displayIndex - 1, { page: "current" }).node();
        const prevData = api.row(displayIndex - 1, { page: "current" }).data();
        const prevWz = prevData[0] || "";
        const prevTimCell = $(prevRowNode).find("td").eq(0);
        const prevTim = prevTimCell.attr("data-tim") || prevTimCell.text().trim();

        if (currentWz === prevWz && currentTim === prevTim && currentTim !== "" && currentTim !== "-") {
          currentTimCell.addClass("tim-cell-merged");
          $(row).removeClass("tim-row-first").addClass("tim-row-subsequent");
        } else {
          currentTimCell.removeClass("tim-cell-merged");
          $(row).removeClass("tim-row-subsequent").addClass("tim-row-first");
        }
      } else {
        currentTimCell.removeClass("tim-cell-merged");
        $(row).removeClass("tim-row-subsequent").addClass("tim-row-first");
      }
    },
  });

  // ─── Chart Options ────────────────────────────────────────────────────────
  const commonOptions = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: {
        beginAtZero: true,
        grid: { color: "rgba(148, 163, 184, 0.16)", drawBorder: false },
        ticks: { precision: 0, color: "#64748b" },
      },
      x: {
        grid: { display: false },
        ticks: { color: "#64748b" },
      },
    },
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: "rgba(15, 23, 42, 0.92)",
        titleColor: "#fff",
        bodyColor: "#e2e8f0",
        padding: 12,
        cornerRadius: 12,
      },
    },
  };

  let psChartInstance = new Chart(document.getElementById("jamPsChart"), {
    type: "line",
    data: {
      labels: jamPs.labels,
      datasets: [{
        label: "Jumlah Order",
        data: jamPs.values,
        borderColor: "rgba(34, 197, 94, 1)",
        backgroundColor: "rgba(34, 197, 94, 0.12)",
        fill: true,
        tension: 0.35,
        pointRadius: 4,
        pointHoverRadius: 5,
        pointBackgroundColor: "#22c55e",
      }],
    },
    options: commonOptions,
  });

  let reChartInstance = new Chart(document.getElementById("jamReChart"), {
    type: "line",
    data: {
      labels: jamRe.labels,
      datasets: [{
        label: "Jumlah Order",
        data: jamRe.values,
        borderColor: "rgba(37, 99, 235, 1)",
        backgroundColor: "rgba(37, 99, 235, 0.12)",
        fill: true,
        tension: 0.35,
        pointRadius: 4,
        pointHoverRadius: 5,
        pointBackgroundColor: "#2563eb",
      }],
    },
    options: commonOptions,
  });

  // ─── Update Dashboard Data (auto refresh) ─────────────────────────────────
  function updateDashboardData() {
    const urlParams = new URLSearchParams(window.location.search);
    const startDate = urlParams.get("start_date") || "";
    const endDate = urlParams.get("end_date") || "";
    const sektor = urlParams.get("sektor") || "";

    fetch(`/api/dashboard/order?start_date=${startDate}&end_date=${endDate}&sektor=${sektor}`)
      .then(res => res.json())
      .then(data => {
        // Update metric cards
        const u = (id, val, bd) => {
          const el = document.getElementById(id);
          if (el) el.textContent = val;
          const bEl = document.getElementById(id.replace("metric-", "") + "-breakdown-container");
          if (bEl && bd) {
            bEl.innerHTML = bd.map(b => `<span class="badge-soft-summary">*${b.product} : ${b.count}</span>`).join("");
          }
        };

        u("metric-total-ps", data.summary.total_ps, data.summary.ps_breakdown);
        u("metric-total-potensi", data.summary.total_potensi, data.summary.potensi_breakdown);
        u("metric-sedang-ogp", data.summary.sedang_ogp, data.summary.ogp_breakdown);
        u("metric-oke-tarik", data.summary.oke_tarik, data.summary.oke_breakdown);
        u("metric-belum-dikerjakan", data.summary.belum_dikerjakan, data.summary.belum_breakdown);
        u("metric-undispatch", data.summary.undispatch, data.summary.undispatch_breakdown);

        // Update Failwa
        const failwaEl = document.getElementById("metric-failwa");
        if (failwaEl && data.failwa_count !== undefined) failwaEl.textContent = data.failwa_count;

        // Update Floating Undispatch
        const floatUnd = document.getElementById("floating-undispatch-count");
        if (floatUnd && data.undispatch_count !== undefined) floatUnd.textContent = data.undispatch_count;

        // Update Charts
        psChartInstance.data.labels = data.jam_ps_chart.labels;
        psChartInstance.data.datasets[0].data = data.jam_ps_chart.values;
        psChartInstance.update();
        document.getElementById("dist-ps-count").textContent = `(${data.jam_ps_chart.total || 0})`;
        if (document.getElementById("dist-ps-breakdown") && data.jam_ps_chart.breakdown) {
            document.getElementById("dist-ps-breakdown").innerHTML = data.jam_ps_chart.breakdown.map(b => `<span class="badge bg-light text-dark border me-1 fw-normal">*${b.product} : ${b.count}</span>`).join('');
        }

        reChartInstance.data.labels = data.jam_re_chart.labels;
        reChartInstance.data.datasets[0].data = data.jam_re_chart.values;
        reChartInstance.update();
        document.getElementById("dist-re-count").textContent = `(${data.jam_re_chart.total || 0})`;
        if (document.getElementById("dist-re-breakdown") && data.jam_re_chart.breakdown) {
            document.getElementById("dist-re-breakdown").innerHTML = data.jam_re_chart.breakdown.map(b => `<span class="badge bg-light text-dark border me-1 fw-normal">*${b.product} : ${b.count}</span>`).join('');
        }

        // Update Sisa Order Pivot Table
        if (data.sisa_pivot) {
          const sp = data.sisa_pivot;
          const tbody = document.getElementById("sisa-pivot-tbody");
          const table = document.getElementById("table-sisa-pivot");
          if (tbody && table) {
            const thead = table.querySelector("thead");
            if (thead) {
              thead.innerHTML = `<tr class="table-light text-uppercase small border-bottom">
                <th style="width: 15%; text-align: left;">Workzone</th>
                <th style="width: 20%; text-align: left;">Wilsus</th>
                ${sp.products.map(p => `<th>${p}</th>`).join('')}
                <th class="bg-light text-dark fw-bold">Grand Total</th>
              </tr>`;
            }

            let bodyHtml = "";
            sp.workzones.forEach(wz => {
              wz.wilsus_rows.forEach((wrow, idx) => {
                const rowspan = wz.wilsus_rows.length + 1;
                const wzTd = idx === 0 ? `<td rowspan="${rowspan}" class="fw-bold align-middle bg-light text-start text-dark" style="font-size: 0.85rem;">${wz.workzone}</td>` : "";
                const pCells = sp.products.map(p => {
                  const val = wrow.product_counts[p] || 0;
                  const cls = val > 0 ? "text-dark fw-bold" : "text-muted opacity-50";
                  return `<td class="${cls}">${val > 0 ? val : '-'}</td>`;
                }).join('');

                bodyHtml += `<tr>
                  ${wzTd}
                  <td class="text-start text-secondary fw-semibold">${wrow.wilsus}</td>
                  ${pCells}
                  <td class="fw-bold text-dark bg-light">${wrow.row_total}</td>
                </tr>`;
              });

              const wzSubtCells = sp.products.map(p => {
                const val = wz.wz_totals[p] || 0;
                const cls = val > 0 ? "text-dark" : "text-muted opacity-50";
                return `<td class="fw-bold ${cls}">${val > 0 ? val : '-'}</td>`;
              }).join('');

              bodyHtml += `<tr class="table-secondary fw-bold">
                <td class="text-start text-uppercase" style="font-size: 0.8rem;">${wz.workzone} Total</td>
                ${wzSubtCells}
                <td class="fw-bold text-dark">${wz.wz_grand_total}</td>
              </tr>`;
            });
            tbody.innerHTML = bodyHtml;

            const tfoot = table.querySelector("tfoot");
            if (tfoot) {
              const footCells = sp.products.map(p => {
                return `<td class="fw-bold text-dark fs-6">${sp.col_totals[p] || 0}</td>`;
              }).join('');
              tfoot.innerHTML = `<tr class="table-light fw-bold text-uppercase" style="border-top: 3px double #94a3b8;">
                <td colspan="2" class="text-start">Grand Total</td>
                ${footCells}
                <td class="fw-bold text-dark fs-6">${sp.grand_total}</td>
              </tr>`;
            }
          }
        }

function cleanCoordinates(coordStr) {
  if (!coordStr || coordStr.trim() === "" || coordStr.trim() === "-") return "";
  const str = coordStr.trim();
  const match = str.match(/(-?\d+)[,\.](\d+)\s*[,\s;:]\s*(1\d+)[,\.](\d+)/);
  if (match) {
    return `${match[1]}.${match[2]},${match[3]}.${match[4]}`;
  }
  const matchStd = str.match(/(-?\d+\.\d+)\s*[,\s]\s*(1\d+\.\d+)/);
  if (matchStd) {
    return `${matchStd[1]},${matchStd[2]}`;
  }
  return str.replace(/\s+/g, "");
}

        // Update Matrix Table (compact: workzone hidden, tim, track_order, odc, status_morning)
        dataTable.clear();
        if (data.matrix_rows) {
          data.matrix_rows.forEach(row => {
            const esc = s => (s || "").toString()
              .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
              .replace(/"/g, "&quot;").replace(/'/g, "&#39;");

            const trackHtml = `<code class="fw-bold text-dark px-2 py-1 bg-light rounded border" style="font-size:0.72rem;">${esc(row.track_order)}</code>${row.is_ps_today ? '<span class="badge bg-success ms-1" style="font-size:0.55rem;">PS</span>' : ''}`;
            
            let odcHtml = `<span class="odc-badge">${esc(row.odc) || "-"}</span>`;
            if (row.kordinat) {
              const coordsClean = cleanCoordinates(row.kordinat);
              if (coordsClean) {
                odcHtml = `<a href="https://www.google.com/maps/search/?api=1&query=${coordsClean}" target="_blank" class="link-maps text-decoration-none" title="Buka Koordinat GPS (${esc(coordsClean)})"><i class="bi bi-geo-alt-fill me-1"></i>${esc(row.odc) || "-"}</a>`;
              }
            }

            const smUpper = (row.status_morning || "").toUpperCase();
            let statusClass = "status-belum";
            if (smUpper.includes("SEDANG")) statusClass = "status-sedang";
            else if (smUpper.includes("OKE")) statusClass = "status-oke";
            else if (smUpper.includes("PENDING") || smUpper.includes("KENDALA") || smUpper.includes("RUSAK")) statusClass = "status-pending";
            else if (smUpper.includes("PS") || smUpper.includes("SETTING")) statusClass = "status-ps";

            const statusHtml = `<span class="badge-soft-status ${statusClass}">${esc(row.status_morning) || "BELUM MAPPED"}</span>`;
            
            const timFlagBadge = row.team_flag === "OGP"
              ? `<span class="badge-team-flag badge-ogp">*OGP</span>`
              : `<span class="badge-team-flag badge-idle">*IDLE</span>`;
            const timHtml = `<span class="fw-bold text-uppercase" style="font-size:0.72rem;color:#1e293b;">${esc(row.tim) || "-"}${timFlagBadge}</span>`;
            const catatanHtml = `<span class="catatan-cell" style="font-size:0.70rem;color:#334155;white-space:pre-wrap;word-break:break-word;">${esc(row.catatan) || ""}</span>`;

            const rowObj = dataTable.row.add([
              row.workzone || "",
              timHtml,
              trackHtml,
              odcHtml,
              statusHtml
            ]);

            const rowNode = rowObj.node();
            $(rowNode).addClass("matrix-compact-row bg-white");
            $($(rowNode).find("td").get(0)).attr("data-tim", row.tim || "");
          });
        }
        dataTable.draw(false);

        // Update Kendala/Pending tables
        const getBadgeHtml = (val) => {
          const normalized = (val || "").toLowerCase().replace(/ /g, "-").replace(/\(/g, "").replace(/\)/g, "").replace(/\//g, "");
          if (!normalized) return `<span class="badge-soft badge-status-empty">${val || "EMPTY"}</span>`;
          return `<span class="badge-soft badge-status-${normalized}">${val || "EMPTY"}</span>`;
        };

        const buildSmallList = (containerId, rowData) => {
          const container = document.getElementById(containerId);
          if (!container) return;
          container.innerHTML = "";
          if (!rowData || rowData.length === 0) {
            container.innerHTML = '<div class="text-center text-muted p-4">Tidak ada data</div>';
          } else {
            rowData.forEach(r => {
              container.innerHTML += `<div class="compact-item">
                <div class="compact-info-row">
                  <div class="compact-tim-track">
                    <span class="compact-tim">${r.tim || "-"}</span>
                    <span class="compact-track" style="font-size:0.62rem;opacity:0.8;">${r.track_order || ""}</span>
                  </div>
                  <div class="compact-status">
                    ${getBadgeHtml(r.status_morning)}
                  </div>
                </div>
                <div class="compact-catatan">${r.catatan || ""}</div>
              </div>`;
            });
          }
        };

        if (data.kendala_fu) {
          const t = document.getElementById("title-kendala");
          if (t) t.textContent = `KENDALA TEKNIK NEED FU (${data.kendala_fu.length})`;
          buildSmallList("kendala-tbody", data.kendala_fu);
        }
        if (data.cek_pending) {
          const t = document.getElementById("title-pending");
          if (t) t.textContent = `CEK PENDING (${data.cek_pending.length})`;
          buildSmallList("cekpending-tbody", data.cek_pending);
        }

        // Update CEK VALIDASI KENDALA Tables
        if (data.kendala_pelanggan) {
          const countEl = document.getElementById("count-kendala-pelanggan");
          if (countEl) countEl.textContent = data.kendala_pelanggan.length;
          const tbody = document.getElementById("tbody-kendala-pelanggan");
          if (tbody) {
            if (data.kendala_pelanggan.length === 0) {
              tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-3">Tidak ada data Kendala Pelanggan</td></tr>';
            } else {
              tbody.innerHTML = data.kendala_pelanggan.map(r => `
                <tr class="bg-white">
                  <td class="fw-bold text-dark">${r.workorder || "-"}</td>
                  <td><code class="fw-bold text-dark px-2 py-1 bg-light rounded border" style="font-size:0.72rem;">${r.track_order || "-"}</code></td>
                  <td><span class="badge-soft-status status-belum">${r.status_morning || "-"}</span></td>
                  <td class="catatan-cell" style="white-space: pre-wrap; word-break: break-word;">${r.catatan || "-"}</td>
                  <td><span class="fw-semibold text-secondary">${r.validasi || "-"}</span></td>
                  <td><span class="fw-bold text-uppercase" style="font-size:0.72rem;">${r.status || "-"}</span></td>
                </tr>
              `).join('');
            }
          }
        }

        if (data.kendala_teknik) {
          const countEl = document.getElementById("count-kendala-teknik");
          if (countEl) countEl.textContent = data.kendala_teknik.length;
          const tbody = document.getElementById("tbody-kendala-teknik");
          if (tbody) {
            if (data.kendala_teknik.length === 0) {
              tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-3">Tidak ada data Kendala Teknik</td></tr>';
            } else {
              tbody.innerHTML = data.kendala_teknik.map(r => `
                <tr class="bg-white">
                  <td class="fw-bold text-dark">${r.workorder || "-"}</td>
                  <td><code class="fw-bold text-dark px-2 py-1 bg-light rounded border" style="font-size:0.72rem;">${r.track_order || "-"}</code></td>
                  <td><span class="badge-soft-status status-pending">${r.status_morning || "-"}</span></td>
                  <td class="catatan-cell" style="white-space: pre-wrap; word-break: break-word;">${r.catatan || "-"}</td>
                  <td><span class="fw-semibold text-secondary">${r.validasi || "-"}</span></td>
                  <td><span class="fw-bold text-uppercase" style="font-size:0.72rem;">${r.status || "-"}</span></td>
                </tr>
              `).join('');
            }
          }
        }

        if (data.detail_potensi) {
          const countEl = document.getElementById("count-detail-potensi");
          if (countEl) countEl.textContent = data.detail_potensi.length;
          const tbody = document.getElementById("tbody-detail-potensi");
          if (tbody) {
            if (data.detail_potensi.length === 0) {
              tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted py-3">Tidak ada data Detail Potensi</td></tr>';
            } else {
              tbody.innerHTML = data.detail_potensi.map(r => `
                <tr class="bg-white">
                  <td class="fw-bold text-dark">${r.workorder || "-"}</td>
                  <td><code class="fw-bold text-dark px-2 py-1 bg-light rounded border" style="font-size:0.72rem;">${r.track_order || "-"}</code></td>
                  <td class="fw-semibold text-secondary">${r.product_name || "-"}</td>
                  <td><span class="odc-badge">${r.odc || "-"}</span></td>
                  <td class="fw-bold text-dark">${r.tim || "-"}</td>
                  <td><span class="badge-soft-status status-ps">${r.status_morning || "-"}</span></td>
                  <td class="catatan-cell" style="white-space: pre-wrap; word-break: break-word;">${r.catatan || "-"}</td>
                  <td><span class="fw-semibold text-secondary" style="font-size:0.72rem;">${r.eskal_daman || "-"}</span></td>
                  <td><span class="fw-bold text-uppercase text-primary" style="font-size:0.72rem;">${r.status || "-"}</span></td>
                </tr>
              `).join('');
            }
          }
        }

        // Update Top TIM panels
        const today_items = data.top_tim_today || [];
        const topTimTodayEl = document.getElementById("top-tim-today");
        if (topTimTodayEl) {
          topTimTodayEl.innerHTML = today_items.length === 0
            ? '<div class="text-center text-muted p-2">Belum ada PS Hari Ini</div>'
            : today_items.map(item => `<div class="d-flex justify-content-between align-items-center px-3 py-2" style="background:rgba(0,0,0,0.04);border-radius:8px;"><span class="fw-medium text-dark" style="font-size:0.95rem;">${item.tim}</span><span class="badge bg-success rounded-pill px-3" style="font-size:0.9rem;">${item.count}</span></div>`).join("");
        }

        const mtd_items = data.top_tim_mtd || [];
        const topTimMtdEl = document.getElementById("top-tim-mtd");
        if (topTimMtdEl) {
          topTimMtdEl.innerHTML = mtd_items.length === 0
            ? '<div class="text-center text-muted p-2">Belum ada PS Bulan Ini</div>'
            : mtd_items.map(item => `<div class="d-flex justify-content-between align-items-center px-3 py-2" style="background:rgba(0,0,0,0.04);border-radius:8px;"><span class="fw-medium text-dark" style="font-size:0.95rem;">${item.tim}</span><span class="badge bg-primary rounded-pill px-3" style="font-size:0.9rem;">${item.count}</span></div>`).join("");
        }

      })
      .catch(err => console.error("Error fetching dashboard data:", err));
  }

  // ─── Metric Card Drilldown ────────────────────────────────────────────────
  let drilldownTable = null;
  const detailModalElement = document.getElementById("detailModal");
  if (detailModalElement) {
    detailModalElement.addEventListener("shown.bs.modal", function () {
      if (drilldownTable) drilldownTable.columns.adjust().draw();
    });
  }

  $(document).on("click", ".metric-card", function () {
    const type = $(this).attr("data-drilldown-type");
    const sektor = new URLSearchParams(window.location.search).get("sektor") || "";
    if (!type) return;

    const isAssurance = type.startsWith("assurance_") || ["rbs_indibiz", "tik_manja", "online_redaman", "hvc_gold", "hvc_diamond", "hvc_platinum", "reguler", "garansi", "osla", "sqm", "unspec", "gamas"].includes(type);

    const titleMap = {
      // Provisioning
      total_ps: "Total PS",
      total_potensi: "Total Potensi",
      sedang_ogp: "Sedang OGP",
      oke_tarik: "Oke Tarik",
      belum_dikerjakan: "Belum Dikerjakan",
      undispatch: "Undispatch",
      idle_teams: "Tim Idle Status",
      perlu_failwa: "Order Perlu Di Failwa",
      // Assurance
      assurance_saldo: "Total Saldo Tiket Assurance",
      rbs_indibiz: "Tiket Assurance: RBS / INDIBIZ",
      tik_manja: "Tiket Assurance: TIKET MANJA (Customer Assign)",
      online_redaman: "Tiket Assurance: ONLINE REDAMAN (< -24 dB)",
      hvc_gold: "Tiket Assurance: PL-TSEL HVC GOLD",
      hvc_diamond: "Tiket Assurance: PL-TSEL HVC DIAMOND",
      hvc_platinum: "Tiket Assurance: PL-TSEL HVC PLATINUM",
      reguler: "Tiket Assurance: PL-TSEL REGULER",
      garansi: "Tiket Assurance: PL-TSEL STATUS GARANSI",
      osla: "Tiket Assurance: PL-TSEL OSLA (TTR > 12 Jam)",
      sqm: "Tiket Assurance: PL-TSEL SQM",
      unspec: "Tiket Assurance: PL-TSEL UNSPEC",
      gamas: "Tiket Assurance: PL-TSEL GAMAS",
      assurance_belum_dikerjakan: "Tiket Assurance: PL-TSEL BELUM DIKERJAKAN",
      assurance_undispatch: "Tiket Assurance: PL-TSEL UNDISPATCH (TANPA TIM)"
    };
    document.getElementById("detailModalLabel").textContent = "Data Detail: " + (titleMap[type] || type.toUpperCase());

    const urlParams = new URLSearchParams(window.location.search);
    const startDate = urlParams.get("start_date") || "";
    const endDate = urlParams.get("end_date") || "";
    const wilsus = urlParams.get("wilsus") || "";
    const jenis_tiket = urlParams.get("jenis_tiket") || "";
    const jenis_order = urlParams.get("jenis_order") || "";

    const fetchUrl = isAssurance
      ? `/api/assurance/detail?category=${type}&sektor=${sektor}&wilsus=${encodeURIComponent(wilsus)}&jenis_tiket=${encodeURIComponent(jenis_tiket)}`
      : `/api/dashboard/detail?start_date=${startDate}&end_date=${endDate}&category=${type}&sektor=${sektor}&wilsus=${encodeURIComponent(wilsus)}&jenis_order=${encodeURIComponent(jenis_order)}`;

    fetch(fetchUrl)
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          if ($.fn.DataTable.isDataTable("#drilldownTable")) {
            $("#drilldownTable").DataTable().destroy();
            $("#drilldownTable").empty();
          }

          if (isAssurance) {
            let theadHtml = `<thead><tr><th>INCIDENT</th><th>ODC REAL</th><th>SERVICE NO</th><th>CUSTOMER SEGMENT</th><th>REPORTED DATE</th><th>CUSTOMER TYPE</th><th>HASIL UKUR</th><th>REDAMAN</th><th>TTR</th><th>FLAG</th><th>TIM</th><th>WILSUS</th><th>STATUS KAWAN</th><th>CATATAN</th><th>JAM MANJA</th><th>SUMMARY</th></tr></thead>`;
            $("#drilldownTable").html(theadHtml + "<tbody></tbody>");

            drilldownTable = $("#drilldownTable").DataTable({
              paging: true, pageLength: 10, searching: true, info: true,
              ordering: false, scrollX: true,
              language: {
                search: "Cari:", lengthMenu: "_MENU_ data",
                info: "_START_ - _END_ dari _TOTAL_ data",
                paginate: { previous: "←", next: "→" },
                zeroRecords: "Tidak ada data tiket", infoEmpty: "Tidak ada data tiket",
                infoFiltered: "(dari _MAX_ total)",
              },
            });

            data.data.forEach(row => {
              drilldownTable.row.add([
                `<code class="fw-bold text-danger">${row.incident}</code>`,
                row.odc_real,
                row.service_no,
                row.customer_segment,
                row.reported_date,
                row.customer_type,
                `<span class="badge bg-secondary">${row.hasil_ukur}</span>`,
                row.redaman,
                row.ttr,
                `<span class="badge bg-info text-dark">${row.flag}</span>`,
                row.tim,
                row.wilsus,
                `<span class="badge bg-light text-dark border">${row.status_kawan}</span>`,
                `<span title="${row.catatan}">${row.catatan}</span>`,
                row.jam_manja,
                `<span title="${row.summary}">${row.summary}</span>`
              ]);
            });
          }
 else {
            const isFailwa = type === "perlu_failwa";
            const isIdle = type === "idle_teams";

            let theadHtml = "";
            if (isFailwa) {
              theadHtml = `<thead><tr><th>STATUS</th><th>TRACK ORDER</th><th>WORKORDER</th><th>STATUS MORNING</th><th>ODC</th><th>JENIS ORDER</th><th>CATATAN</th><th>ESKAL DAMAN</th></tr></thead>`;
            } else if (isIdle) {
              theadHtml = `<thead><tr><th class="text-center">NAMA TIM IDLE (TANPA PEKERJAAN AKTIF)</th></tr></thead>`;
            } else {
              theadHtml = `<thead><tr><th>TRACK ORDER</th><th>WORKORDER</th><th>JENIS ORDER</th><th>ODC</th><th>TIM</th><th>STATUS MORNING</th><th>CATATAN</th><th>ESKAL DAMAN</th></tr></thead>`;
            }

            $("#drilldownTable").html(theadHtml + "<tbody></tbody>");

            drilldownTable = $("#drilldownTable").DataTable({
              paging: true, pageLength: 10, searching: true, info: true,
              ordering: false, scrollX: true,
              language: {
                search: "Cari:", lengthMenu: "_MENU_ data",
                info: "_START_ - _END_ dari _TOTAL_ data",
                paginate: { previous: "←", next: "→" },
                zeroRecords: "Tidak ada data", infoEmpty: "Tidak ada data",
                infoFiltered: "(dari _MAX_ total)",
              },
            });

            const getBadgeHtml = val => {
              const n = (val || "").toLowerCase().replace(/ /g, "-").replace(/[()\/]/g, "");
              if (!n) return `<span class="badge-soft badge-status-empty">${val || "EMPTY"}</span>`;
              return `<span class="badge-soft badge-status-${n}">${val || "EMPTY"}</span>`;
            };

            data.data.forEach(row => {
              if (isFailwa) {
                drilldownTable.row.add([
                  row.status, row.track_order, row.workorder,
                  getBadgeHtml(row.status_morning),
                  row.odc, row.product_name || "-",
                  `<span title="${row.catatan || ""}">${row.catatan || "-"}</span>`,
                  `<span class="fw-semibold text-secondary">${row.eskal_daman || "-"}</span>`
                ]);
              } else if (isIdle) {
                drilldownTable.row.add([
                  `<div class="text-center py-2"><span class="fw-bold fs-6 text-primary">${row.tim}</span></div>`
                ]);
              } else {
                drilldownTable.row.add([
                  row.track_order, row.workorder, row.product_name || "-",
                  row.odc, row.tim,
                  getBadgeHtml(row.status_morning),
                  `<span title="${row.catatan || ""}">${row.catatan || "-"}</span>`,
                  `<span class="fw-semibold text-secondary">${row.eskal_daman || "-"}</span>`
                ]);
              }
            });
          }

          drilldownTable.draw(false);
          const mElement = document.getElementById("detailModal");
          const mInstance = bootstrap.Modal.getOrCreateInstance(mElement);
          mInstance.show();
        }
      })
      .catch(err => console.error("Error fetching detail data:", err));
  });

  // ─── Auto Sync (Refresh on Backend Sync) ───────────────────────────────
  let currentSyncTime = 0;
  
  // Ambil initial sync time saat load
  fetch("/api/status")
    .then(res => res.json())
    .then(data => {
      if (data.last_sync_time) currentSyncTime = data.last_sync_time;
    })
    .catch(err => console.error("Error fetching initial status:", err));

  // Poll status setiap 30 detik untuk mendeteksi perubahan dari n8n
  setInterval(() => {
    if (currentSyncTime === 0) return; // Belum init
    fetch("/api/status")
      .then(res => res.json())
      .then(data => {
        if (data.last_sync_time && data.last_sync_time > currentSyncTime) {
          console.log("New sync detected, reloading page...");
          window.location.reload();
        }
      })
      .catch(err => console.error("Error polling status:", err));
  }, 30000);

  const btnSync = document.getElementById("btnSync");
  const syncText = document.getElementById("syncText");
  if (btnSync) {
    btnSync.addEventListener("click", () => {
      btnSync.disabled = true;
      syncText.textContent = "Syncing...";
      fetch("/api/sync", { method: "POST" })
        .then(res => res.json())
        .then(data => {
          if (data.success) {
            window.location.reload();
          } else {
            console.error("Sync error:", data.message);
          }
        })
        .catch(err => console.error("Sync request failed:", err))
        .finally(() => {
          btnSync.disabled = false;
          syncText.textContent = "Sync Sekarang";
        });
    });
  }

  // ─── Assurance DataTables Init ───────────────────────────────────────────
  if (document.getElementById("assuranceDetailTable")) {
    window.assuranceTable = $("#assuranceDetailTable").DataTable({
      paging: true,
      pageLength: 25,
      searching: true,
      info: true,
      ordering: true,
      order: [[1, "asc"], [0, "asc"]],
      scrollX: false,
      language: {
        search: "Cari Tiket:",
        lengthMenu: "Tampilkan _MENU_ data",
        info: "Menampilkan _START_ sampai _END_ dari _TOTAL_ data",
        paginate: { previous: "←", next: "→" },
        zeroRecords: "Tidak ada data tiket yang cocok",
        infoEmpty: "Tidak ada data tiket",
        infoFiltered: "(difilter dari _MAX_ total data)",
      },
    });
  }

  if (document.getElementById("assuranceMatrixTable")) {
    window.assuranceMatrixTable = $("#assuranceMatrixTable").DataTable({
      paging: false,
      searching: true,
      info: true,
      ordering: false,
      scrollX: false,
      rowGroup: {
        dataSrc: 0,
        startRender: function (rows, group) {
          return $('<tr class="dt-rowgroup-wz"/>')
            .append('<td colspan="8"><div class="d-flex align-items-center"><i class="bi bi-geo-alt-fill text-warning me-2"></i><span class="fw-bold text-uppercase me-2">WORKZONE: ' + (group || "BELUM ADA") + '</span><span class="badge bg-warning text-dark rounded-pill px-3">' + rows.count() + ' TIKET</span></div></td>');
        }
      },


      columnDefs: [
        { targets: [0], visible: false }
      ],
      language: {
        search: "Cari Matriks Tiket:",
        info: "Total _TOTAL_ data matriks tiket",
        zeroRecords: "Tidak ada data matriks tiket",
        infoEmpty: "Tidak ada data matriks tiket",
      },
      rowCallback: function (row, data, displayNum, displayIndex) {
        // Keep team names visible on every row without merging
        const currentTimCell = $(row).find("td").eq(0);
        currentTimCell.removeClass("tim-cell-merged");
        $(row).removeClass("tim-row-subsequent").addClass("tim-row-first");
      },
    });
  }

  // ─── Click Handler for Pivot Table Cells (Provisioning & Assurance) ───────
  $(document).on("click", ".clickable-pivot-cell", function () {
    const module = $(this).attr("data-module");
    const wz = $(this).attr("data-wz") || "";
    const wilsus = $(this).attr("data-wilsus") || "";
    const jenis = $(this).attr("data-jenis") || "";
    const cnt = parseInt($(this).attr("data-cnt") || "0", 10);

    if (cnt === 0) return;

    const isAssurance = (module === "assurance");
    const label = `${isAssurance ? "Assurance" : "Provisioning"} Detail: Workzone ${wz}${wilsus && wilsus !== '-' ? ' (' + wilsus + ')' : ''} - ${jenis}`;
    document.getElementById("detailModalLabel").textContent = label;

    const urlParams = new URLSearchParams(window.location.search);
    const sektor = urlParams.get("sektor") || "";
    const startDate = urlParams.get("start_date") || "";
    const endDate = urlParams.get("end_date") || "";

    const fetchUrl = isAssurance
      ? `/api/assurance/detail?category=pivot_cell&workzone=${encodeURIComponent(wz)}&wilsus=${encodeURIComponent(wilsus)}&jenis=${encodeURIComponent(jenis)}&sektor=${encodeURIComponent(sektor)}`
      : `/api/dashboard/detail?category=pivot_cell&workzone=${encodeURIComponent(wz)}&wilsus=${encodeURIComponent(wilsus)}&jenis=${encodeURIComponent(jenis)}&sektor=${encodeURIComponent(sektor)}&start_date=${startDate}&end_date=${endDate}`;

    fetch(fetchUrl)
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          if ($.fn.DataTable.isDataTable("#drilldownTable")) {
            $("#drilldownTable").DataTable().destroy();
            $("#drilldownTable").empty();
          }

          if (isAssurance) {
            let theadHtml = `<thead><tr><th>INCIDENT</th><th>ODC REAL</th><th>SERVICE NO</th><th>CUSTOMER SEGMENT</th><th>REPORTED DATE</th><th>CUSTOMER TYPE</th><th>HASIL UKUR</th><th>REDAMAN</th><th>TTR</th><th>FLAG</th><th>TIM</th><th>WILSUS</th><th>STATUS KAWAN</th><th>CATATAN</th><th>JAM MANJA</th><th>SUMMARY</th></tr></thead>`;
            $("#drilldownTable").html(theadHtml + "<tbody></tbody>");

            const dt = $("#drilldownTable").DataTable({
              paging: true, pageLength: 10, searching: true, info: true,
              ordering: false, scrollX: true,
              language: {
                search: "Cari:", lengthMenu: "_MENU_ data",
                info: "_START_ - _END_ dari _TOTAL_ data",
                paginate: { previous: "←", next: "→" },
                zeroRecords: "Tidak ada data tiket", infoEmpty: "Tidak ada data tiket"
              }
            });

            data.data.forEach(row => {
              dt.row.add([
                `<code class="fw-bold text-danger">${row.incident}</code>`,
                row.odc_real,
                row.service_no,
                row.customer_segment,
                row.reported_date,
                row.customer_type,
                `<span class="badge bg-secondary">${row.hasil_ukur}</span>`,
                row.redaman,
                row.ttr,
                `<span class="badge bg-info text-dark">${row.flag}</span>`,
                row.tim,
                row.wilsus,
                `<span class="badge bg-light text-dark border">${row.status_kawan}</span>`,
                `<span title="${row.catatan}">${row.catatan}</span>`,
                row.jam_manja,
                `<span title="${row.summary}">${row.summary}</span>`
              ]);
            });
            dt.draw();
          } else {
            let theadHtml = `<thead><tr><th>TRACK ORDER</th><th>WORKORDER</th><th>JENIS ORDER</th><th>ODC</th><th>TIM</th><th>STATUS MORNING</th><th>CATATAN</th><th>ESKAL DAMAN</th></tr></thead>`;
            $("#drilldownTable").html(theadHtml + "<tbody></tbody>");

            const dt = $("#drilldownTable").DataTable({
              paging: true, pageLength: 10, searching: true, info: true,
              ordering: false, scrollX: true,
              language: {
                search: "Cari:", lengthMenu: "_MENU_ data",
                info: "_START_ - _END_ dari _TOTAL_ data",
                paginate: { previous: "←", next: "→" },
                zeroRecords: "Tidak ada data order", infoEmpty: "Tidak ada data order"
              }
            });

            data.data.forEach(row => {
              dt.row.add([
                `<code class="fw-bold text-primary">${row.track_order}</code>`,
                row.workorder,
                `<span class="badge bg-light text-dark border">${row.product_name}</span>`,
                row.odc,
                row.tim,
                `<span class="badge bg-info bg-opacity-20 text-dark">${row.status_morning}</span>`,
                `<span title="${row.catatan}">${row.catatan}</span>`,
                row.eskal_daman
              ]);
            });
            dt.draw();
          }
          const bsModal = new bootstrap.Modal(document.getElementById("detailModal"));
          bsModal.show();
        }
      });
  });

  // ─── Auto Sync (Setiap 16 Menit) ─────────────────────────────────────────
  setInterval(() => {
    if (btnSync && !btnSync.disabled) {
      console.log("Auto-sync triggered (16 menit)");
      btnSync.click();
    }
  }, 16 * 60 * 1000); // 16 Menit
})();



