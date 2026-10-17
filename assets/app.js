(function () {
  "use strict";

  var set, KEY, state, cards;

  function el(tag, cls, html) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html !== undefined) e.innerHTML = html;
    return e;
  }

  function load() {
    var s = null;
    try { s = JSON.parse(localStorage.getItem(KEY)); } catch (e) {}
    return s && s.answers ? s : { answers: {}, checked: {} };
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
    if (q.type === "num") return !!state.checked[q.n];
    return state.answers[q.n] !== undefined;
  }

  function label(v) { return v === true ? "True" : v === false ? "False" : String(v); }

  // ---------- Set selection ----------
  function pick(id) {
    set = window.SETS.find(function (s) { return s.id === id; }) || window.SETS[0];
    KEY = "dsi-set-" + set.id;
    state = load();
    cards = {};
    document.title = set.title + " · DSI Practice";
    document.querySelectorAll("#tabs a").forEach(function (a) {
      a.setAttribute("aria-current", a.dataset.id === set.id ? "page" : "false");
    });
    render();
  }

  function tabs() {
    var nav = document.getElementById("tabs");
    window.SETS.forEach(function (s) {
      var a = el("a", "", s.title + ' <span class="count">' + s.questions.length + "</span>");
      a.href = "#" + s.id;
      a.dataset.id = s.id;
      nav.appendChild(a);
    });
  }

  // ---------- Rendering ----------
  function render() {
    var quiz = document.getElementById("quiz");
    quiz.innerHTML = "";
    set.parts.forEach(function (part) {
      var range = part.from === part.to ? "Question " + part.from : "Questions " + part.from + "–" + part.to;
      quiz.appendChild(el("div", "part-head", "<h2>" + part.name + "</h2><p>" + range + " · " + part.note + "</p>"));
      set.questions.slice(part.from - 1, part.to).forEach(function (q) { quiz.appendChild(card(q)); });
    });
    set.questions.forEach(paint);
    progress();
  }

  function card(q) {
    var c = el("article", "q");
    c.id = "q" + q.n;
    c.appendChild(el("div", "q-head", '<span class="num">Question ' + q.n + '</span><span class="tag"></span>'));
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
        if (ev.key === "Enter") check(q);
      });
      var btn = el("button", "check", "Check");
      btn.type = "button";
      btn.addEventListener("click", function () { check(q); });
      row.appendChild(input);
      row.appendChild(btn);
      c.appendChild(row);
    } else {
      var group = el("div", "tf");
      [true, false].forEach(function (v) {
        var b = el("button", "", label(v));
        b.type = "button";
        b.dataset.value = String(v);
        b.addEventListener("click", function () {
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
    progress();
  }

  function paint(q) {
    var c = cards[q.n];
    var graded = isGraded(q);
    var ok = graded && isCorrect(q);
    c.classList.toggle("graded", graded);
    c.classList.toggle("correct", ok);
    c.classList.toggle("wrong", graded && !ok);
    c.querySelector(".tag").textContent = graded ? q.topic : "";

    if (q.type !== "num") {
      c.querySelectorAll(".tf button").forEach(function (b) {
        var v = b.dataset.value === "true";
        b.setAttribute("aria-pressed", String(state.answers[q.n] === v));
        b.classList.toggle("is-answer", v === q.answer);
      });
    }

    var fb = c.querySelector(".feedback");
    if (graded) {
      var ans = q.type === "num" ? q.answer.toLocaleString("en-US") : label(q.answer);
      fb.innerHTML = '<span class="verdict">' + (ok ? "Correct." : "Incorrect.") + "</span> Answer: <b>" + ans + "</b>. " + q.why;
    } else {
      fb.innerHTML = "";
    }
  }

  function progress() {
    var done = set.questions.filter(isGraded).length;
    document.getElementById("progress").textContent = done + " / " + set.questions.length + " answered";
  }

  // ---------- Controls ----------
  document.getElementById("reset").addEventListener("click", function () {
    if (!confirm("Clear all answers in " + set.title + "?")) return;
    state = { answers: {}, checked: {} };
    save();
    render();
    window.scrollTo({ top: 0 });
  });

  window.addEventListener("hashchange", function () {
    pick(location.hash.slice(1));
    window.scrollTo({ top: 0 });
  });

  tabs();
  pick(location.hash.slice(1));
})();
