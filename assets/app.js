(function () {
  "use strict";

  var params = new URLSearchParams(location.search);
  var exam = window.EXAMS.find(function (e) { return String(e.id) === params.get("id"); }) || window.EXAMS[0];
  var KEY = "dsi-exam-" + exam.id;
  var BEST = "dsi-best-" + exam.id;

  var PARTS = [
    { name: "Part 1 · True/False: Modules", note: "Questions 1–20 · 1 point each", test: function (q) { return q.n <= 20; } },
    { name: "Part 2 · Numeric", note: "Questions 21–25 are 2 points; 26–30 are 3 points. Enter an exact whole number.", test: function (q) { return q.type === "num"; } },
    { name: "Part 3 · True/False: Papers", note: "Questions 31–35 · 1 point each", test: function (q) { return q.n >= 31 && q.n <= 35; } },
    { name: "Acknowledgement", note: "Question 36 · 0 points", test: function (q) { return q.type === "ack"; } }
  ];

  var state = load();
  var cards = {};

  document.title = exam.title + " · DSI Mock Exams";
  document.getElementById("title").textContent = exam.title;

  function load() {
    var s = null;
    try { s = JSON.parse(localStorage.getItem(KEY)); } catch (e) {}
    return s && s.answers ? s : { answers: {}, checked: {}, mode: "exam", submitted: false };
  }

  function save() {
    try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {}
  }

  function parseNum(v) {
    var t = String(v == null ? "" : v).replace(/[,\s_]/g, "");
    return /^-?\d+$/.test(t) ? Number(t) : null;
  }

  function isCorrect(q) {
    var a = state.answers[q.n];
    if (q.type === "num") return parseNum(a) === q.answer;
    return a === q.answer;
  }

  function isGraded(q) {
    if (state.submitted) return true;
    if (state.mode !== "study") return false;
    if (q.type === "num") return !!state.checked[q.n];
    return state.answers[q.n] !== undefined;
  }

  function label(v) { return v === true ? "True" : v === false ? "False" : String(v); }

  function el(tag, cls, html) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html !== undefined) e.innerHTML = html;
    return e;
  }

  // ---------- Rendering ----------
  function render() {
    var quiz = document.getElementById("quiz");
    quiz.innerHTML = "";
    PARTS.forEach(function (part) {
      var qs = exam.questions.filter(part.test);
      var head = el("div", "part-head", "<h2>" + part.name + "</h2><p>" + part.note + "</p>");
      head.dataset.part = part.name;
      quiz.appendChild(head);
      qs.forEach(function (q) { quiz.appendChild(card(q)); });
    });
    paintAll();
  }

  function card(q) {
    var c = el("article", "q");
    c.id = "q" + q.n;
    var pts = q.points === 1 ? "1 pt" : q.points + " pts";
    c.appendChild(el("div", "q-head",
      '<span class="num">Question ' + q.n + "</span><span>" + pts + '</span><span class="tag"></span>'));
    c.appendChild(el("p", "q-text", q.text));

    if (q.type === "num") {
      var row = el("div", "numrow");
      var input = el("input");
      input.type = "text";
      input.inputMode = "numeric";
      input.autocomplete = "off";
      input.setAttribute("aria-label", "Answer to question " + q.n);
      input.value = state.answers[q.n] || "";
      input.addEventListener("input", function () {
        state.answers[q.n] = input.value;
        delete state.checked[q.n];
        save();
        paint(q);
        progress();
      });
      input.addEventListener("keydown", function (ev) {
        if (ev.key === "Enter" && state.mode === "study") check(q);
      });
      var btn = el("button", "check", "Check");
      btn.type = "button";
      btn.addEventListener("click", function () { check(q); });
      row.appendChild(input);
      row.appendChild(btn);
      c.appendChild(row);
    } else {
      var opts = q.type === "ack" ? ["Yes", "No"] : [true, false];
      var group = el("div", "tf");
      opts.forEach(function (v) {
        var b = el("button", "", label(v));
        b.type = "button";
        b.dataset.value = String(v);
        b.addEventListener("click", function () {
          if (state.submitted) return;
          state.answers[q.n] = v;
          save();
          paint(q);
          progress();
        });
        group.appendChild(b);
      });
      c.appendChild(group);
    }
    c.appendChild(el("div", "feedback"));
    cards[q.n] = c;
    return c;
  }

  function check(q) {
    if (parseNum(state.answers[q.n]) === null) return;
    state.checked[q.n] = true;
    save();
    paint(q);
  }

  function paint(q) {
    var c = cards[q.n];
    var graded = isGraded(q);
    var ok = graded && isCorrect(q);
    c.classList.toggle("graded", graded);
    c.classList.toggle("correct", ok);
    c.classList.toggle("wrong", graded && !ok);
    c.querySelector(".tag").textContent = graded ? q.topic : "";

    if (q.type === "num") {
      var input = c.querySelector("input");
      input.disabled = state.submitted;
      var btn = c.querySelector(".check");
      btn.style.display = state.mode === "study" && !state.submitted ? "" : "none";
    } else {
      c.querySelectorAll(".tf button").forEach(function (b) {
        var v = q.type === "ack" ? b.dataset.value : b.dataset.value === "true";
        b.setAttribute("aria-pressed", String(state.answers[q.n] === v));
        b.classList.toggle("is-answer", v === q.answer);
        b.disabled = state.submitted;
      });
    }

    var fb = c.querySelector(".feedback");
    if (graded) {
      var given = state.answers[q.n];
      var unanswered = given === undefined || given === "";
      var verdict = ok ? "Correct." : unanswered ? "Not answered." : "Incorrect.";
      var ans = q.type === "num" ? q.answer.toLocaleString("en-US") : label(q.answer);
      fb.innerHTML = '<span class="verdict">' + verdict + "</span> Answer: <b>" + ans + "</b>. " + q.why;
    } else {
      fb.innerHTML = "";
    }
  }

  function paintAll() {
    exam.questions.forEach(paint);
    document.querySelectorAll(".seg button").forEach(function (b) {
      b.setAttribute("aria-pressed", String(b.dataset.mode === state.mode));
      b.disabled = state.submitted;
    });
    document.getElementById("submit").disabled = state.submitted;
    progress();
    result();
  }

  function progress() {
    var graded = exam.questions.filter(function (q) { return q.points > 0; });
    var done = graded.filter(function (q) {
      var a = state.answers[q.n];
      return a !== undefined && a !== "";
    }).length;
    document.getElementById("progress").textContent = done + " / " + graded.length + " answered";
  }

  // ---------- Scoring ----------
  function score() {
    var rows = PARTS.slice(0, 3).map(function (part) {
      var qs = exam.questions.filter(part.test);
      var got = 0, max = 0, right = 0;
      qs.forEach(function (q) {
        max += q.points;
        if (isCorrect(q)) { got += q.points; right += 1; }
      });
      return { name: part.name, right: right, count: qs.length, got: got, max: max };
    });
    var total = rows.reduce(function (s, r) { return s + r.got; }, 0);
    var missed = {};
    exam.questions.forEach(function (q) {
      if (q.points > 0 && !isCorrect(q)) missed[q.topic] = (missed[q.topic] || 0) + 1;
    });
    return { rows: rows, total: total, missed: missed };
  }

  function result() {
    var box = document.getElementById("result");
    if (!state.submitted) {
      box.classList.remove("show");
      box.innerHTML = "";
      return;
    }
    var s = score();
    var pct = Math.round((s.total / 50) * 100);
    var html = '<div class="score">' + s.total + " / 50 <small>(" + pct + "%)</small></div>";
    html += "<table><thead><tr><th>Part</th><th>Correct</th><th>Points</th></tr></thead><tbody>";
    s.rows.forEach(function (r) {
      html += "<tr><td>" + r.name + "</td><td>" + r.right + " / " + r.count + "</td><td>" + r.got + " / " + r.max + "</td></tr>";
    });
    html += "</tbody></table>";
    var topics = Object.keys(s.missed).sort(function (a, b) { return s.missed[b] - s.missed[a]; });
    if (topics.length) {
      html += '<p class="hint">Missed by topic: ' + topics.map(function (t) { return t + " (" + s.missed[t] + ")"; }).join(" · ") + "</p>";
    } else {
      html += '<p class="hint">Every graded question correct.</p>';
    }
    html += '<div class="actions"><button type="button" id="only-missed">Show only missed</button>' +
            '<button type="button" id="retake">Retake exam</button></div>';
    box.innerHTML = html;
    box.classList.add("show");

    var quiz = document.getElementById("quiz");
    var btn = document.getElementById("only-missed");
    btn.textContent = quiz.classList.contains("hide-correct") ? "Show all questions" : "Show only missed";
    btn.addEventListener("click", function () {
      quiz.classList.toggle("hide-correct");
      markEmptyParts();
      btn.textContent = quiz.classList.contains("hide-correct") ? "Show all questions" : "Show only missed";
    });
    document.getElementById("retake").addEventListener("click", reset);
    markEmptyParts();
  }

  function markEmptyParts() {
    document.querySelectorAll(".part-head").forEach(function (head) {
      var part = PARTS.find(function (p) { return p.name === head.dataset.part; });
      var allRight = exam.questions.filter(part.test).every(isCorrect);
      head.classList.toggle("all-correct", allRight);
    });
  }

  function reset() {
    state = { answers: {}, checked: {}, mode: state.mode, submitted: false };
    save();
    document.getElementById("quiz").classList.remove("hide-correct");
    render();
    window.scrollTo({ top: 0 });
  }

  // ---------- Controls ----------
  document.querySelectorAll(".seg button").forEach(function (b) {
    b.addEventListener("click", function () {
      if (state.submitted) return;
      state.mode = b.dataset.mode;
      save();
      paintAll();
    });
  });

  document.getElementById("submit").addEventListener("click", function () {
    var unanswered = exam.questions.filter(function (q) {
      var a = state.answers[q.n];
      return q.points > 0 && (a === undefined || a === "");
    }).length;
    if (unanswered && !confirm(unanswered + " question" + (unanswered > 1 ? "s are" : " is") + " unanswered and will be marked wrong. Submit anyway?")) return;
    state.submitted = true;
    save();
    var total = score().total;
    try {
      var best = Number(localStorage.getItem(BEST));
      if (localStorage.getItem(BEST) === null || total > best) localStorage.setItem(BEST, String(total));
    } catch (e) {}
    paintAll();
    window.scrollTo({ top: 0, behavior: "smooth" });
  });

  document.getElementById("reset").addEventListener("click", function () {
    if (confirm("Clear all answers for this exam?")) reset();
  });

  render();
})();
