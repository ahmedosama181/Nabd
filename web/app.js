/* Nabd - front end (English / Arabic). Text from the API goes in via textContent only. */
(function () {
  "use strict";

  // ------------------------------------------------------------------ strings
  const MONTHS = {
    en: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    enLong: ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
    ar: ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"],
  };
  const T = {
    en: {
      title: "Nabd", tagline: "Egyptian pound market pulse", docTitle: "Nabd · Egyptian pound market pulse",
      subtitle: (from, to, upd) => `Year to date · ${from} – ${to} · updated ${upd}`,
      refresh: "Refresh", csv: "CSV", karat: "Gold karat", theme: "Switch theme",
      themes: { auto: "Auto", light: "Light", dark: "Dark" },
      tabPrice: "Price", tabCompare: "Compare all", tabMonth: "Month by month",
      details: "More details", detailsSub: "all numbers, what moved prices, Egyptian gold shops, daily data",
      disclaimer: "For information only, not financial advice.",
      contact: "Contact", license: "MIT License",
      saveChart: "Save image",
      ago: (m) => (m < 1 ? "just now" : m < 60 ? `${m} min ago` : `${Math.round(m / 60)} h ago`),
      live: {
        tag: "LIVE", gold: "Gold ounce", silver: "Silver ounce", goldEgp: (k) => `Gold ${k}k now`, shop: (k) => `Shops, ${k}k`,
        sells: "sell", buys: "buy", today: "today", oz: "USD/oz", g: "EGP/g", at: (x) => `at ${x}`,
        info: "Live global gold and silver prices from gold-api.com, refreshed every minute while this page is open and converted with the latest dollar rate. Shop prices come from an Egyptian gold price site and refresh every 10 minutes.",
      },
      insights: {
        atHigh: (n) => [n, " is at its highest price this year."],
        atLow: (n) => [n, " is at its lowest price this year."],
        fromPeak: (n, hi, d, p) => [n, " peaked at ", hi, " on ", d, " and is now ", p, " lower."],
        streakUp: (n, k) => [n, ": up ", k, " days in a row."],
        streakDown: (n, k) => [n, ": down ", k, " days in a row."],
        jumpy: (n, v) => ["Most jumpy: ", n, ". It moves about ", v, " on a typical day."],
        calm: (n, v) => ["Most stable: ", n, ", about ", v, " a day."],
        bestMonth: (n, m, v) => ["Biggest monthly jump: ", n, " in ", m, " (", v, ")."],
      },
      calc: {
        title: "How much is it worth?", have: "I have", spend: "My budget", amount: "Amount", budget: "Budget (EGP)",
        items: { gold_24: "grams of gold 24k", gold_21: "grams of gold 21k", gold_18: "grams of gold 18k", pound: "gold pounds (8 g of 21k)",
                 silver: "grams of silver", usd: "US dollars", eur: "euros", gbp: "British pounds" },
        worth: "Worth today", shopBuys: "A gold shop would pay about", onBase: (d) => `On ${d}:`, egp: "EGP",
        budgetLead: "At today's prices this buys about:",
        note: "Based on the latest prices on this page. Shops add their own margin when they sell.",
      },
      whatif: {
        title: "What if?", amount: "Amount (EGP)", cash: "Kept as cash",
        lead: (d) => `If you had put this amount into each one on ${d}, today you would have:`,
      },
      backup: "The main price source didn't answer, so a backup source was used. Small differences are normal.",
      sourceNames: { daily: "currency-api daily rates (jsDelivr / Cloudflare)", yahoo: "Yahoo Finance (backup)", frankfurter: "Frankfurter / ECB (backup)" },
      liveLine: "Live gold and silver: gold-api.com",
      names: { usd: "US Dollar", eur: "Euro", gbp: "British Pound", gold: (k) => `Gold ${k}k`, silver: "Silver" },
      units: { usd: "EGP per dollar", eur: "EGP per euro", gbp: "EGP per pound", gold: "EGP per gram", silver: "EGP per gram" },
      up: "up", down: "down", flat: "no change",
      thisYear: "this year",
      lastDay: "Last day:",
      loading: "Updating prices…",
      firstRun: "Updating prices… the first run of the year downloads every day since 1 January and can take a minute or two.",
      loadError: (m) => (m === "no-connection" ? "Could not download prices. Check your internet connection and press Refresh." : `Could not load prices: ${m}. Check your internet connection and press Refresh.`),
      refreshFailed: () => "Refresh failed. Showing the prices you already have.",
      offline: "Could not reach the price sources. Showing the last saved prices.",
      partial: "Some sources did not answer this time. Missing days will be added on the next refresh.",
      noTrading: "No trading days yet this year. The price shown is the 31 December close.",
      summaryMixed: (b, bp, w, wp, since) => [`Since ${since}, the biggest rise is `, b, " (", bp, ") and the biggest fall is ", w, " (", wp, ")."],
      summaryAllUp: (b, bp, since) => [`Since ${since}, every price is up. The biggest rise is `, b, " (", bp, ")."],
      summaryAllDown: (w, wp, since) => [`Since ${since}, every price is down. The biggest fall is `, w, " (", wp, ")."],
      poundStronger: (p) => [" The Egyptian pound got ", "stronger", ": a dollar costs ", p, " less."],
      poundWeaker: (p) => [" The Egyptian pound got ", "weaker", ": a dollar costs ", p, " more."],
      notePrice: (d) => `The dashed line is the price on ${d}. Above it = more expensive than at the start of the year.`,
      noteCompare: (d) => `Every line starts at 100 on ${d}, so you can compare them fairly: 110 means +10%, 90 means −10%.`,
      noteMonth: "Each bar is how much the price changed during that month (from the last day of the previous month).",
      tipSince: (d) => `since ${d}`, tipPrevDay: "vs previous day", soFar: "so far",
      indexAxis: "Start of year = 100", pctAxis: "% change in the month",
      // details
      hKpi: "All numbers", leadKpi: "Point at (or tap) the ⓘ next to a column to see what it means.", leadKpiNarrow: "What each number means is explained under the list.",
      colAsset: "Asset", colLatest: "Latest", colYtd: "Since 31 Dec", col1d: "1 day", col7d: "7 days", col30d: "30 days",
      colHigh: "Highest", colLow: "Lowest", colAvg: "Average", colVol: "Daily swing", colDd: "Biggest drop", colBest: "Best month", colWorst: "Worst month",
      tips: {
        ytd: "How much the price changed since the last price of last year (31 December).",
        d1: "Change compared with the previous trading day.",
        d7: "Change compared with 7 days ago.", d30: "Change compared with 30 days ago.",
        high: "Highest price this year and the day it happened.", low: "Lowest price this year and the day it happened.",
        avg: "Average daily price this year.",
        vol: "How jumpy the price is: the typical size of one day's move. Higher = riskier.",
        dd: "The biggest fall from a previous high this year.",
        best: "The calendar month with the biggest rise.", worst: "The calendar month with the biggest fall.",
      },
      goldGlobal: "Gold, global (USD per ounce)", silverGlobal: "Silver, global (USD per ounce)",
      hMonth: "Month by month", colMonth: "Month", wholePeriod: "Since 31 Dec",
      hDrivers: "What moved the price in pounds?",
      leadDrivers: "A price in Egyptian pounds moves for two reasons: the global price (in dollars) and the price of the dollar in pounds. The two multiply together.",
      colInEgp: "Change in EGP", colGlobal: "Global price", colFx: "Dollar in pounds",
      driverBase: { eur: "Euro vs dollar", gbp: "Pound sterling vs dollar", gold: "Gold in dollars", silver: "Silver in dollars" },
      hLocal: "Egyptian gold shops today",
      leadLocal: "Today's prices at Egyptian gold shops, compared with the price you get from the global gold price and the dollar rate. A small gap is normal (shop margin, timing of the dollar rate).",
      colKarat: "Karat", colSell: "Shop sells at", colBuy: "Shop buys at", colImplied: "From global price", colGap: "Difference",
      localSource: (s, t) => `Source: ${s}, read ${t}.`, localStale: " These are the last prices that could be read.",
      localError: "The local gold price pages could not be read right now. Everything else is unaffected.",
      hData: "Daily data", showData: "Show the daily table", colDate: "Date",
      hHow: "How the numbers are calculated",
      how: [
        "Gold and silver in pounds = global price in dollars per ounce × dollar price in pounds ÷ 31.1035 (grams in an ounce). Gold 21k = 24k × 21/24. Silver is pure (999). A gold pound is 8 grams of 21k.",
        "Daily prices are the rates published once a day by currency-api (spot prices). Live prices at the top come from gold-api.com.",
        "Euro and pound sterling in pounds = their price in dollars × dollar price in pounds.",
        "The year starts from the last price of 31 December. Month by month compares each month's last price with the previous month's last price.",
        "Weekends and holidays have no new prices; the last known price is carried forward in the charts.",
        "Only this year's prices are kept on your computer. On 1 January the saved prices are cleared and the new year starts.",
      ],
      hSources: "Data sources",
      sourceLine: (l, s) => `${l}: ${s || "not available"}`,
      localLine: (s) => `Local gold prices: ${s || "not available"}`,
      footSources: (s) => `Data: ${s}`,
    },
    ar: {
      title: "نبض", tagline: "نبض أسعار الجنيه المصري", docTitle: "نبض · نبض أسعار الجنيه المصري",
      subtitle: (from, to, upd) => `منذ بداية العام · ${from} – ${to} · آخر تحديث ${upd}`,
      refresh: "تحديث", csv: "تنزيل CSV", karat: "عيار الذهب", theme: "تغيير المظهر",
      themes: { auto: "تلقائي", light: "فاتح", dark: "داكن" },
      tabPrice: "السعر", tabCompare: "مقارنة الكل", tabMonth: "شهراً بشهر",
      details: "تفاصيل أكثر", detailsSub: "كل الأرقام، ما الذي حرّك الأسعار، محلات الذهب في مصر، البيانات اليومية",
      disclaimer: "للعلم فقط، وليست نصيحة مالية.",
      contact: "للتواصل", license: "رخصة MIT",
      saveChart: "حفظ كصورة",
      ago: (m) => {
        if (m < 1) return "الآن";
        if (m < 60) return m === 1 ? "منذ دقيقة" : m === 2 ? "منذ دقيقتين" : m <= 10 ? `منذ ${m} دقائق` : `منذ ${m} دقيقة`;
        const hr = Math.round(m / 60);
        return hr === 1 ? "منذ ساعة" : hr === 2 ? "منذ ساعتين" : hr <= 10 ? `منذ ${hr} ساعات` : `منذ ${hr} ساعة`;
      },
      live: {
        tag: "مباشر", gold: "أوقية الذهب", silver: "أوقية الفضة", goldEgp: (k) => `ذهب عيار ${k} الآن`, shop: (k) => `المحلات، عيار ${k}`,
        sells: "بيع", buys: "شراء", today: "اليوم", oz: "دولار/أوقية", g: "جنيه/جرام", at: (x) => `الساعة ${x}`,
        info: "أسعار الذهب والفضة العالمية المباشرة من gold-api.com، تتحدث كل دقيقة طالما الصفحة مفتوحة ومحوّلة بآخر سعر للدولار. أسعار المحلات من موقع مصري لأسعار الذهب وتتحدث كل 10 دقائق.",
      },
      insights: {
        atHigh: (n) => ["أعلى سعر هذا العام الآن: ", n, "."],
        atLow: (n) => ["أدنى سعر هذا العام الآن: ", n, "."],
        fromPeak: (n, hi, d, p) => [n, ": أعلى سعر هذا العام ", hi, " في ", d, "، والسعر الآن أقل بنسبة ", p, "."],
        streakUp: (n, k) => [n, ": ارتفاع ", k, k <= 10 ? " أيام متتالية." : " يوماً متتالياً."],
        streakDown: (n, k) => [n, ": انخفاض ", k, k <= 10 ? " أيام متتالية." : " يوماً متتالياً."],
        jumpy: (n, v) => ["الأكثر تقلباً: ", n, " (حركة يومية معتادة نحو ", v, ")."],
        calm: (n, v) => ["الأكثر استقراراً: ", n, " (نحو ", v, " يومياً)."],
        bestMonth: (n, m, v) => ["أكبر قفزة شهرية: ", n, " في ", m, " (", v, ")."],
      },
      calc: {
        title: "كم تساوي؟", have: "عندي", spend: "ميزانيتي", amount: "الكمية", budget: "الميزانية (جنيه)",
        items: { gold_24: "جرام ذهب عيار 24", gold_21: "جرام ذهب عيار 21", gold_18: "جرام ذهب عيار 18", pound: "جنيه ذهب (8 جرام عيار 21)",
                 silver: "جرام فضة", usd: "دولار أمريكي", eur: "يورو", gbp: "جنيه إسترليني" },
        worth: "قيمتها اليوم", shopBuys: "محل الذهب سيشتريها بنحو", onBase: (d) => `في ${d}:`, egp: "جنيه",
        budgetLead: "بأسعار اليوم يمكنك شراء نحو:",
        note: "حسب آخر الأسعار في هذه الصفحة. المحلات تضيف هامشها عند البيع.",
      },
      whatif: {
        title: "ماذا لو؟", amount: "المبلغ (جنيه)", cash: "احتفظت به نقداً",
        lead: (d) => `لو وضعت هذا المبلغ في كل واحد منها في ${d}، لكان معك اليوم:`,
      },
      backup: "مصدر الأسعار الرئيسي لم يستجب، لذلك استُخدم مصدر احتياطي. الفروق الصغيرة طبيعية.",
      sourceNames: { daily: "currency-api – أسعار يومية (jsDelivr / Cloudflare)", yahoo: "Yahoo Finance (احتياطي)", frankfurter: "Frankfurter / البنك المركزي الأوروبي (احتياطي)" },
      liveLine: "الذهب والفضة المباشر: gold-api.com",
      names: { usd: "الدولار الأمريكي", eur: "اليورو", gbp: "الجنيه الإسترليني", gold: (k) => `ذهب عيار ${k}`, silver: "الفضة" },
      units: { usd: "جنيه لكل دولار", eur: "جنيه لكل يورو", gbp: "جنيه لكل إسترليني", gold: "جنيه للجرام", silver: "جنيه للجرام" },
      up: "ارتفاع", down: "انخفاض", flat: "بدون تغيير",
      thisYear: "هذا العام",
      lastDay: "آخر يوم:",
      loading: "جارٍ تحديث الأسعار…",
      firstRun: "جارٍ تحديث الأسعار… أول تشغيل في العام يحمّل كل الأيام منذ 1 يناير وقد يستغرق دقيقة أو دقيقتين.",
      loadError: (m) => (m === "no-connection" ? "تعذّر تنزيل الأسعار. تأكد من الاتصال بالإنترنت ثم اضغط تحديث." : `تعذّر تحميل الأسعار: ${m}. تأكد من الاتصال بالإنترنت ثم اضغط تحديث.`),
      refreshFailed: () => "فشل التحديث. يتم عرض الأسعار المحفوظة.",
      offline: "تعذّر الوصول لمصادر الأسعار. يتم عرض آخر أسعار محفوظة.",
      partial: "بعض المصادر لم تستجب هذه المرة. الأيام الناقصة ستُضاف في التحديث القادم.",
      noTrading: "لا توجد أيام تداول بعد هذا العام. السعر المعروض هو سعر إغلاق 31 ديسمبر.",
      summaryMixed: (b, bp, w, wp, since) => [`منذ ${since}، الأكثر ارتفاعاً: `, b, " (", bp, ")، والأكثر انخفاضاً: ", w, " (", wp, ")."],
      summaryAllUp: (b, bp, since) => [`منذ ${since}، كل الأسعار ارتفعت، والأكثر ارتفاعاً: `, b, " (", bp, ")."],
      summaryAllDown: (w, wp, since) => [`منذ ${since}، كل الأسعار انخفضت، والأكثر انخفاضاً: `, w, " (", wp, ")."],
      poundStronger: (p) => [" الجنيه المصري أصبح ", "أقوى", " أمام الدولار: الدولار أرخص بنسبة ", p, "."],
      poundWeaker: (p) => [" الجنيه المصري أصبح ", "أضعف", " أمام الدولار: الدولار أغلى بنسبة ", p, "."],
      notePrice: (d) => `الخط المتقطع هو السعر في ${d}. فوقه = أغلى من بداية العام.`,
      noteCompare: (d) => `كل الخطوط تبدأ من 100 في ${d} لتسهيل المقارنة: 110 تعني +10%، و90 تعني −10%.`,
      noteMonth: "كل عمود يوضح نسبة تغير السعر خلال الشهر (مقارنةً بآخر يوم في الشهر السابق).",
      tipSince: (d) => `منذ ${d}`, tipPrevDay: "مقارنةً باليوم السابق", soFar: "حتى الآن",
      indexAxis: "بداية العام = 100", pctAxis: "نسبة التغير في الشهر",
      hKpi: "كل الأرقام", leadKpi: "مرّر المؤشر على ⓘ بجانب العمود (أو اضغط عليه) لمعرفة معناه.", leadKpiNarrow: "شرح معنى كل رقم موجود أسفل القائمة.",
      colAsset: "الأصل", colLatest: "آخر سعر", colYtd: "منذ 31 ديسمبر", col1d: "يوم", col7d: "7 أيام", col30d: "30 يوماً",
      colHigh: "أعلى سعر", colLow: "أدنى سعر", colAvg: "المتوسط", colVol: "التذبذب اليومي", colDd: "أكبر هبوط", colBest: "أفضل شهر", colWorst: "أسوأ شهر",
      tips: {
        ytd: "نسبة تغير السعر منذ آخر سعر في العام الماضي (31 ديسمبر).",
        d1: "التغير مقارنةً بيوم التداول السابق.",
        d7: "التغير مقارنةً بما قبل 7 أيام.", d30: "التغير مقارنةً بما قبل 30 يوماً.",
        high: "أعلى سعر هذا العام واليوم الذي حدث فيه.", low: "أدنى سعر هذا العام واليوم الذي حدث فيه.",
        avg: "متوسط السعر اليومي هذا العام.",
        vol: "مدى تقلب السعر: الحجم المعتاد لحركة يوم واحد. كلما زاد كان أكثر مخاطرة.",
        dd: "أكبر هبوط من أعلى سعر سابق خلال العام.",
        best: "الشهر الذي شهد أكبر ارتفاع.", worst: "الشهر الذي شهد أكبر انخفاض.",
      },
      goldGlobal: "الذهب عالمياً (دولار للأوقية)", silverGlobal: "الفضة عالمياً (دولار للأوقية)",
      hMonth: "شهراً بشهر", colMonth: "الشهر", wholePeriod: "منذ 31 ديسمبر",
      hDrivers: "ما الذي حرّك السعر بالجنيه؟",
      leadDrivers: "يتغير السعر بالجنيه المصري لسببين: السعر العالمي (بالدولار)، وسعر الدولار بالجنيه. والأثران يتضاعفان معاً.",
      colInEgp: "التغير بالجنيه", colGlobal: "السعر العالمي", colFx: "سعر الدولار بالجنيه",
      driverBase: { eur: "اليورو مقابل الدولار", gbp: "الإسترليني مقابل الدولار", gold: "الذهب بالدولار", silver: "الفضة بالدولار" },
      hLocal: "محلات الذهب في مصر اليوم",
      leadLocal: "أسعار اليوم في محلات الذهب المصرية، مقارنةً بالسعر المحسوب من السعر العالمي وسعر الدولار. الفرق الصغير طبيعي (هامش المحل وتوقيت سعر الدولار).",
      colKarat: "العيار", colSell: "سعر البيع", colBuy: "سعر الشراء", colImplied: "من السعر العالمي", colGap: "الفرق",
      localSource: (s, t) => `المصدر: ${s}، تمت القراءة ${t}.`, localStale: " هذه آخر أسعار أمكن قراءتها.",
      localError: "تعذّرت قراءة صفحات أسعار الذهب المحلية حالياً. باقي الصفحة لا يتأثر.",
      hData: "البيانات اليومية", showData: "عرض الجدول اليومي", colDate: "التاريخ",
      hHow: "كيف تُحسب الأرقام",
      how: [
        "الذهب والفضة بالجنيه = السعر العالمي بالدولار للأوقية × سعر الدولار بالجنيه ÷ 31.1035 (عدد الجرامات في الأوقية). عيار 21 = عيار 24 × 21/24. الفضة نقية (999). الجنيه الذهب = 8 جرام عيار 21.",
        "الأسعار اليومية هي الأسعار التي ينشرها currency-api مرة يومياً (أسعار فورية). الأسعار المباشرة أعلى الصفحة من gold-api.com.",
        "اليورو والإسترليني بالجنيه = سعرهما بالدولار × سعر الدولار بالجنيه.",
        "يبدأ العام من آخر سعر في 31 ديسمبر. مقارنة الشهور تقارن آخر سعر في كل شهر بآخر سعر في الشهر السابق.",
        "لا توجد أسعار جديدة في العطلات ونهاية الأسبوع؛ يُستخدم آخر سعر معروف في الرسوم.",
        "يتم حفظ أسعار هذا العام فقط على جهازك. في 1 يناير تُمسح الأسعار المحفوظة ويبدأ العام الجديد.",
      ],
      hSources: "مصادر البيانات",
      sourceLine: (l, s) => `${l}: ${s || "غير متاح"}`,
      localLine: (s) => `أسعار الذهب المحلية: ${s || "غير متاح"}`,
      footSources: (s) => `البيانات: ${s}`,
    },
  };
  const SYMBOL_AR = { "GC=F": "الذهب (دولار للأوقية)", "SI=F": "الفضة (دولار للأوقية)", "EGP=X": "الدولار/الجنيه", "EURUSD=X": "اليورو/الدولار", "GBPUSD=X": "الإسترليني/الدولار" };

  // Fixed identity -> colour slot (validated order; never re-assigned when something is hidden).
  const SERIES = [{ id: "usd", slot: 1 }, { id: "eur", slot: 2 }, { id: "gbp", slot: 3 }, { id: "gold", slot: 4 }, { id: "silver", slot: 5 }];

  // ------------------------------------------------------------------ state
  const $ = (id) => document.getElementById(id);
  const store = {
    get(k, d) { try { return localStorage.getItem(k) || d; } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* storage blocked */ } },
  };
  const IDS = ["usd", "eur", "gbp", "gold", "silver"];
  const CALC_ITEMS = ["gold_24", "gold_21", "gold_18", "pound", "silver", "usd", "eur", "gbp"];
  const pick = (v, ok, d) => (ok.includes(v) ? v : d);
  let shown = null;
  try { shown = JSON.parse(store.get("shown", "null")); } catch (e) { shown = null; }
  shown = Array.isArray(shown) ? shown.filter((x) => IDS.includes(x)) : [];
  const state = {
    data: null, chart: null, live: null, loading: false,
    lang: pick(store.get("lang", "en"), ["en", "ar"], "en"),
    karat: pick(store.get("karat", "21"), ["24", "21", "18"], "21"),
    theme: pick(store.get("theme", "auto"), ["auto", "light", "dark"], "auto"),
    tab: pick(store.get("tab", "price"), ["price", "compare", "month"], "price"),
    focus: pick(store.get("focus", "gold"), IDS, "gold"),
    shown: new Set(shown.length ? shown : IDS),
    calcMode: pick(store.get("calcMode", "have"), ["have", "spend"], "have"),
    calcItem: pick(store.get("calcItem", "gold_21"), CALC_ITEMS, "gold_21"),
    calcAmount: store.get("calcAmount", "10"),
    budget: store.get("budget", "10000"),
    whatif: store.get("whatif", "10000"),
  };
  const t = () => T[state.lang];
  const isRtl = () => state.lang === "ar"; // in Arabic, time runs right to left (31 Dec on the right)

  // ------------------------------------------------------------------ helpers
  function h(tag, attrs, ...kids) {
    const el = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (v == null || v === false) continue;
      if (k === "class") el.className = v; else el.setAttribute(k, v === true ? "" : v);
    }
    for (const kid of kids.flat()) if (kid != null && kid !== false) el.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
    return el;
  }
  const LRI = "⁦", PDI = "⁩"; // keep numbers left-to-right inside Arabic text drawn on canvas
  const nf = (v, d) => (v == null ? "–" : new Intl.NumberFormat("en-US", { minimumFractionDigits: d, maximumFractionDigits: d }).format(v));
  const pct = (v, d = 1) => (v == null ? "–" : (v > 0 ? "+" : v < 0 ? "−" : "") + nf(Math.abs(v), d) + "%");
  const num = (text, cls) => h("span", { class: "num" + (cls ? " " + cls : "") }, text);
  const cssVar = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
  const color = (slot) => cssVar("--series-" + slot);
  const dateParts = (s) => s.split("-").map(Number);
  function fmtDate(s, withYear = true) {
    const [y, m, d] = dateParts(s);
    return d + " " + MONTHS[state.lang === "ar" ? "ar" : "en"][m - 1] + (withYear ? " " + y : "");
  }
  function fmtMonth(ym, long) {
    const [y, m] = dateParts(ym + "-01");
    return (state.lang === "ar" ? MONTHS.ar : long ? MONTHS.enLong : MONTHS.en)[m - 1] + (long ? " " + y : "");
  }
  const fmtTime = (isoStr) => {
    const d = new Date(isoStr);
    return fmtDate(d.getFullYear() + "-" + (d.getMonth() + 1) + "-" + d.getDate(), false) + " " + String(d.getHours()).padStart(2, "0") + ":" + String(d.getMinutes()).padStart(2, "0");
  };
  const OUNCE_G = 31.1034768;
  // Amounts typed by people: accept Arabic-Indic digits, Arabic separators and thousands separators.
  function parseAmount(text) {
    const s = String(text || "")
      .replace(/[٠-٩]/g, (d) => String("٠١٢٣٤٥٦٧٨٩".indexOf(d)))
      .replace(/[۰-۹]/g, (d) => String("۰۱۲۳۴۵۶۷۸۹".indexOf(d)))
      .replace(/٫/g, ".").replace(/[٬,\s]/g, "");
    const v = Number(s);
    return s !== "" && isFinite(v) && v >= 0 ? v : null;
  }
  const keyOf = (id) => (id === "gold" ? "gold_" + state.karat : id);
  const asset = (key) => state.data.assets.find((a) => a.key === key);
  const nameOf = (id) => (id === "gold" ? t().names.gold(state.karat) : t().names[id]);
  const active = () => SERIES.filter((s) => asset(keyOf(s.id)));
  const dir = (v) => (v == null || Math.abs(v) < 0.005 ? "flat" : v > 0 ? "up" : "down");
  const arrow = (v) => ({ up: "▲", down: "▼", flat: "■" })[dir(v)];
  const baseDate = () => fmtDate(state.data.period.base_date);
  function hint(text) { return h("button", { type: "button", class: "hint", "aria-label": text, "data-tip": text }, "i"); }
  function pill(v) {
    const d = dir(v);
    return h("span", { class: "pill " + d }, arrow(v) + " ", t()[d] + " ", num(pct(Math.abs(v || 0)).replace(/^[+−]/, "")));
  }
  function theme() {
    return { surfaceSolid: cssVar("--surface-solid"), ink: cssVar("--ink"), ink2: cssVar("--ink-2"), ink3: cssVar("--ink-3"), grid: cssVar("--grid"), surface: cssVar("--surface"), line: cssVar("--line") };
  }

  // ------------------------------------------------------------------ language / theme
  function applyLang() {
    const L = state.lang;
    document.documentElement.lang = L;
    document.documentElement.dir = L === "ar" ? "rtl" : "ltr";
    document.title = t().docTitle;
    document.querySelectorAll("[data-i18n]").forEach((el) => { el.textContent = t()[el.dataset.i18n]; });
    document.querySelectorAll("[data-lang]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.lang === L)));
    $("theme-label").textContent = t().themes[state.theme];
    $("theme").setAttribute("aria-label", t().theme + ": " + t().themes[state.theme]); // labels are icon-only on phones
    $("save-chart").setAttribute("aria-label", t().saveChart);
    $("csv").setAttribute("aria-label", t().csv);
    document.documentElement.dataset.mode = state.theme;
    $("theme").title = t().theme;
    $("csv").href = "/api/export.csv?lang=" + L;
    [...$("karat").options].forEach((o) => { o.textContent = L === "ar" ? o.value : o.value + "k"; });
  }
  function applyTheme() {
    if (state.theme === "auto") document.documentElement.removeAttribute("data-theme");
    else document.documentElement.setAttribute("data-theme", state.theme);
  }

  // ------------------------------------------------------------------ loading
  async function load(refresh, quiet) {
    if (state.loading) return;
    state.loading = true;
    const btn = $("refresh"), status = $("status"), progress = $("progress");
    btn.disabled = true;
    if (!quiet) progress.hidden = false;
    if (state.data) { if (!quiet) $("content").classList.add("loading"); }
    else { status.hidden = false; status.classList.remove("error"); status.textContent = t().loading; $("skeleton").hidden = false; }
    const slow = setTimeout(() => { if (!state.data) status.textContent = t().firstRun; }, 3500);
    try {
      const res = await fetch("/api/data" + (refresh ? "?refresh=1" : ""));
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "HTTP " + res.status);
      const first = !state.data;
      state.data = body;
      status.hidden = true;
      $("skeleton").hidden = true;
      $("content").hidden = false;
      render();
      if (first) { pollLive(); setTimeout(() => document.body.classList.add("settled"), 1800); }
    } catch (err) {
      if (!state.data) { $("skeleton").hidden = true; status.hidden = false; status.classList.add("error"); status.textContent = t().loadError(err.message); }
      else if (!quiet) banner(t().refreshFailed(err.message));
    } finally {
      clearTimeout(slow);
      state.loading = false;
      btn.disabled = false; progress.hidden = true;
      $("content").classList.remove("loading");
    }
  }
  function banner(text) { $("banners").append(h("div", { class: "banner", role: "status" }, text)); }

  // ------------------------------------------------------------------ render
  function render() {
    if (!state.data) return;
    const d = state.data;
    $("banners").replaceChildren();
    if (d.notice) banner(t()[d.notice] || d.notice);
    if (Object.values(d.sources).some((s) => s === "yahoo" || s === "frankfurter")) banner(t().backup);
    if (d.assets.every((a) => a.kpis.n_days === 0)) banner(t().noTrading);
    d.warnings.forEach((w) => banner(w));
    updateAgo();
    const used = [...new Set(Object.values(d.sources).filter(Boolean))].map((s) => ({ daily: "currency-api", yahoo: "Yahoo Finance", frankfurter: "Frankfurter" })[s] || s);
    $("foot-sources").textContent = t().footSources(used.concat(["gold-api.com", d.local && d.local.source].filter(Boolean)).join(" · "));
    renderSummary();
    renderInsights();
    renderCards();
    renderTabs();
    renderChart();
    renderCalc();
    renderWhatIf();
    renderLive();
    if ($("details").open) renderDetails();
  }

  function renderSummary() {
    const rows = active().map((s) => ({ id: s.id, v: asset(keyOf(s.id)).kpis.change_pct }));
    rows.sort((a, b) => b.v - a.v);
    const best = rows[0], worst = rows[rows.length - 1], since = baseDate();
    const b = (x) => h("b", {}, nameOf(x.id));
    let parts;
    if (best.v > 0 && worst.v < 0) parts = t().summaryMixed(b(best), num(pct(best.v)), b(worst), num(pct(worst.v)), since);
    else if (worst.v >= 0) parts = t().summaryAllUp(b(best), num(pct(best.v)), since);
    else parts = t().summaryAllDown(b(worst), num(pct(worst.v)), since);
    const usd = asset("usd");
    if (usd && Math.abs(usd.kpis.change_pct) >= 0.05) {
      const p = num(pct(Math.abs(usd.kpis.change_pct)).slice(1));
      const s = usd.kpis.change_pct < 0 ? t().poundStronger(p) : t().poundWeaker(p);
      s[1] = h("b", {}, s[1]);
      parts = parts.concat(s);
    }
    $("summary").replaceChildren(...parts);
  }

  function sparkline(key, c) {
    const vals = state.data.grid.series[key].filter((v) => v != null);
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 100 32"); svg.setAttribute("preserveAspectRatio", "none"); svg.setAttribute("aria-hidden", "true");
    if (vals.length < 2) return svg;
    const min = Math.min(...vals), max = Math.max(...vals), span = max - min || 1;
    const pts = vals.map((v, i) => ((isRtl() ? 1 - i / (vals.length - 1) : i / (vals.length - 1)) * 100).toFixed(2) + "," + (30 - ((v - min) / span) * 28).toFixed(2)).join(" ");
    const area = document.createElementNS(svg.namespaceURI, "polygon");
    area.setAttribute("points", (isRtl() ? "100,32 " : "0,32 ") + pts + (isRtl() ? " 0,32" : " 100,32"));
    area.setAttribute("fill", c); area.setAttribute("opacity", "0.10");
    const line = document.createElementNS(svg.namespaceURI, "polyline");
    line.setAttribute("points", pts); line.setAttribute("fill", "none"); line.setAttribute("stroke", c);
    line.setAttribute("stroke-width", "2"); line.setAttribute("stroke-linejoin", "round"); line.setAttribute("vector-effect", "non-scaling-stroke");
    svg.append(area, line);
    return svg;
  }

  let counted = false; // numbers count up from the 31 Dec price only on the first render
  function countUp(el, from, to, dec) {
    if (counted || matchMedia("(prefers-reduced-motion: reduce)").matches) { el.textContent = nf(to, dec); return; }
    const t0 = performance.now(), dur = 900;
    const step = (now) => {
      const p = Math.min(1, (now - t0) / dur), e = 1 - Math.pow(1 - p, 3);
      el.textContent = nf(from + (to - from) * e, dec);
      if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }
  function renderCards() {
    const wrap = $("cards");
    wrap.replaceChildren();
    for (const s of active()) {
      const a = asset(keyOf(s.id)), k = a.kpis, c = color(s.slot);
      const priceEl = num(nf(k.start, a.decimals));
      countUp(priceEl, k.start, k.end, a.decimals);
      const card = h("button", { type: "button", class: "kcard", style: "--c:" + c, "data-id": s.id, "aria-pressed": String(state.tab === "price" && state.focus === s.id) },
        h("span", { class: "kname" }, h("span", { class: "dot" }), nameOf(s.id)),
        h("span", { class: "kunit" }, t().units[s.id]),
        h("span", { class: "kprice" }, priceEl),
        h("span", { class: "krow" }, pill(k.change_pct), h("span", { class: "kunit kyear" }, t().thisYear)),
        h("span", { class: "kfrom" }, fmtDate(k.start_date) + ": ", num(nf(k.start, a.decimals))),
        sparkline(a.key, c),
        h("span", { class: "ktoday" }, t().lastDay + " ", num(pct(k.change_1d_pct, 2))));
      card.addEventListener("click", () => {
        state.focus = s.id; state.tab = "price"; store.set("focus", s.id); store.set("tab", "price");
        syncCards(); renderTabs(); renderChart();
        $("chart").closest(".main").scrollIntoView({ behavior: reduceMotion() ? "auto" : "smooth", block: "nearest" });
      });
      card.style.setProperty("--i", String(wrap.children.length));
      wrap.append(card);
    }
    counted = true;
  }
  function syncCards() {
    document.querySelectorAll(".kcard").forEach((c) => c.setAttribute("aria-pressed", String(state.tab === "price" && state.focus === c.dataset.id)));
  }

  function renderTabs() {
    document.querySelectorAll("#tabs [data-tab]").forEach((b) => b.setAttribute("aria-selected", String(b.dataset.tab === state.tab)));
    const chips = $("chips");
    chips.replaceChildren();
    for (const s of active()) {
      const on = state.tab === "price" ? state.focus === s.id : state.shown.has(s.id);
      const chip = h("button", { type: "button", class: "chip", style: "--c:" + color(s.slot), "aria-pressed": String(on) }, h("i"), nameOf(s.id));
      chip.addEventListener("click", () => {
        if (state.tab === "price") { state.focus = s.id; store.set("focus", s.id); syncCards(); }
        else {
          if (state.shown.has(s.id) && state.shown.size > 1) state.shown.delete(s.id); else state.shown.add(s.id);
          store.set("shown", JSON.stringify([...state.shown]));
        }
        renderTabs(); renderChart();
      });
      chips.append(chip);
    }
  }

  // ------------------------------------------------------------------ the one chart
  function ticksFor(dates, T) {
    const step = window.innerWidth < 560 ? 3 : window.innerWidth < 900 ? 2 : 1; // fewer month labels on small screens
    return {
      grid: { display: false }, border: { color: T.line }, reverse: isRtl(),
      ticks: {
        color: T.ink3, autoSkip: false, maxRotation: 0, align: "inner", font: { size: 11 },
        callback: (v, i) => {
          if (i === 0) return fmtDate(dates[0], false);
          const m = dates[i].slice(0, 7);
          return m !== dates[i - 1].slice(0, 7) && i > 2 && (Number(m.slice(5)) - 1) % step === 0 ? fmtMonth(m) : "";
        },
      },
    };
  }
  const crosshair = (T) => ({
    id: "crosshair",
    afterDatasetsDraw(chart) {
      const act = chart.tooltip && chart.tooltip.getActiveElements ? chart.tooltip.getActiveElements() : [];
      if (!act.length || chart.config.type !== "line") return;
      const x = act[0].element.x, a = chart.chartArea, c = chart.ctx;
      c.save(); c.strokeStyle = T.ink3; c.lineWidth = 1; c.setLineDash([3, 3]);
      c.beginPath(); c.moveTo(x, a.top); c.lineTo(x, a.bottom); c.stroke(); c.restore();
    },
  });
  const hline = (T, value) => ({
    id: "hline",
    beforeDatasetsDraw(chart) {
      if (value == null) return;
      const y = chart.scales.y.getPixelForValue(value), a = chart.chartArea, c = chart.ctx;
      if (y < a.top || y > a.bottom) return;
      c.save(); c.strokeStyle = T.ink3; c.lineWidth = 1; c.setLineDash(chart.config.type === "bar" ? [] : [5, 4]);
      c.beginPath(); c.moveTo(a.left, y); c.lineTo(a.right, y); c.stroke(); c.restore();
    },
  });
  function tooltipBase(T) {
    return {
      backgroundColor: T.surfaceSolid, titleColor: T.ink, bodyColor: T.ink2, footerColor: T.ink3, borderColor: T.line, borderWidth: 1,
      padding: 12, boxWidth: 12, boxHeight: 3, cornerRadius: 10, titleFont: { weight: "600", size: 13 }, bodyFont: { size: 12.5 }, bodySpacing: 5,
      rtl: state.lang === "ar", textDirection: state.lang === "ar" ? "rtl" : "ltr", caretPadding: 8,
    };
  }
  const wrapNum = (s) => LRI + s + PDI;
  const reduceMotion = () => matchMedia("(prefers-reduced-motion: reduce)").matches;
  // soft glow under each line (drawn with the canvas shadow, so it costs nothing when idle)
  const glow = {
    id: "glow",
    beforeDatasetDraw(chart, args) {
      const ds = chart.data.datasets[args.index];
      chart.ctx.save();
      chart.ctx.shadowColor = (ds.borderColor || "#000") + "99";
      chart.ctx.shadowBlur = 12;
      chart.ctx.shadowOffsetY = 4;
    },
    afterDatasetDraw(chart) { chart.ctx.restore(); },
  };
  const fadeFill = (c) => (ctx) => {
    const area = ctx.chart.chartArea;
    if (!area) return c + "22";
    const grad = ctx.chart.ctx.createLinearGradient(0, area.top, 0, area.bottom);
    grad.addColorStop(0, c + "66");
    grad.addColorStop(0.6, c + "14");
    grad.addColorStop(1, c + "00");
    return grad;
  };

  // Labelled dots on the year's highest and lowest price (price view). Labels stay inside the plot.
  const extremes = (T, vals, dates, dec, c) => ({
    id: "extremes",
    afterDatasetsDraw(chart) {
      let ih = -1, il = -1;
      vals.forEach((v, i) => {
        if (v == null || i === 0) return; // index 0 is the 31 Dec starting point, not this year
        if (ih < 0 || v > vals[ih]) ih = i;
        if (il < 0 || v < vals[il]) il = i;
      });
      if (ih < 0 || ih === il) return;
      const pts = chart.getDatasetMeta(0).data, ctx = chart.ctx, area = chart.chartArea;
      const mark = (i, up) => {
        const p = pts[i];
        if (!p) return;
        const text = (up ? "▲ " : "▼ ") + wrapNum(nf(vals[i], dec)) + " · " + fmtDate(dates[i], false);
        ctx.save();
        ctx.direction = isRtl() ? "rtl" : "ltr";
        ctx.font = "600 11.5px -apple-system, Segoe UI, Roboto, sans-serif";
        const w = ctx.measureText(text).width + 14, hgt = 20;
        const x = Math.min(Math.max(p.x, area.left + w / 2 + 2), area.right - w / 2 - 2);
        let y = up ? p.y - 18 : p.y + 18;
        y = Math.min(Math.max(y, area.top + hgt / 2 + 1), area.bottom - hgt / 2 - 1);
        ctx.fillStyle = c; ctx.strokeStyle = T.surfaceSolid; ctx.lineWidth = 2;
        ctx.beginPath(); ctx.arc(p.x, p.y, 4.5, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
        ctx.fillStyle = T.surfaceSolid; ctx.strokeStyle = c; ctx.lineWidth = 1;
        ctx.beginPath();
        if (ctx.roundRect) ctx.roundRect(x - w / 2, y - hgt / 2, w, hgt, 10); else ctx.rect(x - w / 2, y - hgt / 2, w, hgt);
        ctx.fill(); ctx.stroke();
        ctx.fillStyle = T.ink; ctx.textAlign = "center"; ctx.textBaseline = "middle";
        ctx.fillText(text, x, y + 0.5);
        ctx.restore();
      };
      mark(ih, true);
      mark(il, false);
    },
  });

  function renderChart() {
    const T = theme(), g = state.data.grid, act = active();
    if (state.chart) { state.chart.destroy(); state.chart = null; }
    const opts = {
      responsive: true, maintainAspectRatio: false,
      animation: reduceMotion() ? false : { duration: 700, easing: "easeOutQuart" },
      transitions: { resize: { animation: { duration: 0 } } },
      layout: { padding: { left: 6, right: 6 } },
      interaction: { mode: "index", intersect: false },
      plugins: { legend: { display: false }, tooltip: tooltipBase(T) },
      locale: "en-US",
    };
    let config;
    const canvas = $("chart");

    if (state.tab === "price") {
      const s = act.find((x) => x.id === state.focus) || act[0];
      const a = asset(keyOf(s.id)), vals = g.series[a.key], base = vals.find((v) => v != null), c = color(s.slot);
      opts.plugins.tooltip.callbacks = {
        title: (it) => fmtDate(g.dates[it[0].dataIndex]),
        label: (it) => " " + wrapNum(nf(it.parsed.y, a.decimals)) + "  " + t().units[s.id],
        afterLabel: (it) => {
          const i = it.dataIndex; let j = i - 1;
          while (j >= 0 && vals[j] == null) j--;
          const out = [wrapNum(pct((it.parsed.y / base - 1) * 100, 2)) + "  " + t().tipSince(baseDate())];
          if (j >= 0) out.push(wrapNum(pct((it.parsed.y / vals[j] - 1) * 100, 2)) + "  " + t().tipPrevDay);
          return out;
        },
      };
      opts.scales = {
        x: ticksFor(g.dates, T),
        y: { grid: { color: T.grid }, border: { display: false }, position: state.lang === "ar" ? "right" : "left",
             ticks: { color: T.ink3, maxTicksLimit: 6, font: { size: 11 }, callback: (v) => wrapNum(nf(v, a.decimals && Math.abs(v) < 1000 ? 1 : 0)) } },
      };
      config = { type: "line", data: { labels: g.dates, datasets: [{
        label: nameOf(s.id), data: vals, borderColor: c, borderWidth: 2, pointRadius: 0, pointHoverRadius: 5, pointHoverBackgroundColor: c,
        pointHoverBorderColor: T.surface, pointHoverBorderWidth: 2, tension: 0, spanGaps: true,
        fill: "start", backgroundColor: fadeFill(c) }] }, options: opts, plugins: [hline(T, base), glow, extremes(T, vals, g.dates, a.decimals, c), crosshair(T)] };
      canvas.setAttribute("aria-label", nameOf(s.id));
      $("chart-note").textContent = t().notePrice(baseDate());
    } else if (state.tab === "compare") {
      const shown = act.filter((s) => state.shown.has(s.id));
      const ds = shown.map((s) => {
        const vals = g.series[keyOf(s.id)], base = vals.find((v) => v != null), c = color(s.slot);
        return { label: nameOf(s.id), data: vals.map((v) => (v == null ? null : (v / base) * 100)), borderColor: c, backgroundColor: c,
          borderWidth: 2, pointRadius: 0, pointHoverRadius: 4, pointHoverBorderColor: T.surface, pointHoverBorderWidth: 2, tension: 0, spanGaps: true };
      });
      opts.plugins.tooltip.callbacks = {
        title: (it) => fmtDate(g.dates[it[0].dataIndex]),
        label: (it) => " " + it.dataset.label + "  " + wrapNum(pct(it.parsed.y - 100, 2)),
      };
      opts.plugins.tooltip.itemSort = (a, b) => b.parsed.y - a.parsed.y;
      opts.plugins.tooltip.footer = () => t().tipSince(baseDate());
      opts.scales = {
        x: ticksFor(g.dates, T),
        y: { grid: { color: T.grid }, border: { display: false }, position: state.lang === "ar" ? "right" : "left",
             ticks: { color: T.ink3, font: { size: 11 }, callback: (v) => wrapNum(nf(v, 0)) }, title: { display: true, text: t().indexAxis, color: T.ink3, font: { size: 11 } } },
      };
      config = { type: "line", data: { labels: g.dates, datasets: ds }, options: opts, plugins: [hline(T, 100), glow, crosshair(T)] };
      canvas.setAttribute("aria-label", t().tabCompare);
      $("chart-note").textContent = t().noteCompare(baseDate());
    } else {
      const shown = act.filter((s) => state.shown.has(s.id));
      const months = asset(keyOf(act[0].id)).kpis.monthly;
      const narrow = window.innerWidth < 700; // thin bars: no separator border, or it would hide the fill
      const ds = shown.map((s) => {
        const m = asset(keyOf(s.id)).kpis.monthly, c = color(s.slot);
        return { label: nameOf(s.id), data: months.map((mo) => { const r = m.find((x) => x.month === mo.month); return r ? r.change_pct : null; }),
          backgroundColor: c, borderColor: T.surfaceSolid, borderWidth: narrow ? 0 : 2, borderRadius: narrow ? 2 : 4, borderSkipped: false, maxBarThickness: 28,
          categoryPercentage: narrow ? 0.86 : 0.8, barPercentage: narrow ? 0.92 : 0.9 };
      });
      opts.plugins.tooltip.callbacks = {
        title: (it) => { const mo = months[it[0].dataIndex]; return fmtMonth(mo.month, true) + (mo.partial ? " (" + t().soFar + ")" : ""); },
        label: (it) => " " + it.dataset.label + "  " + wrapNum(pct(it.parsed.y, 2)),
      };
      opts.scales = {
        x: { grid: { display: false }, border: { display: false }, reverse: isRtl(), ticks: { color: T.ink2, font: { size: 12 }, maxRotation: 0, autoSkip: true, autoSkipPadding: 6,
             callback: (v, i) => fmtMonth(months[i].month) + (months[i].partial ? "*" : "") } },
        y: { grid: { color: T.grid }, border: { display: false }, position: state.lang === "ar" ? "right" : "left",
             ticks: { color: T.ink3, font: { size: 11 }, callback: (v) => wrapNum((v < 0 ? "−" : "") + nf(Math.abs(v), 0) + "%") }, title: { display: true, text: t().pctAxis, color: T.ink3, font: { size: 11 } } },
      };
      config = { type: "bar", data: { labels: months.map((m) => m.month), datasets: ds }, options: opts, plugins: [hline(T, 0)] };
      canvas.setAttribute("aria-label", t().tabMonth);
      $("chart-note").textContent = t().noteMonth + (months.some((m) => m.partial) ? "  * " + t().soFar : "");
    }
    if (window.Chart) {
      state.chart = new Chart(canvas, config);
      requestAnimationFrame(fitChart);
      setTimeout(fitChart, 900); // after the entrance animation
    }
  }

  // ------------------------------------------------------------------ details (built only when opened)
  function table(head, rows, cls) {
    const ths = head.map((x) => h("th", {}, x));
    const labels = head.map((x) => [x].flat().filter((y) => typeof y === "string").join(" ").replace(/^[=×]\s*/, "").trim());
    rows.forEach((tr) => [...tr.children].forEach((td, i) => {
      td.setAttribute("data-label", labels[i] || "");
      if (td.childNodes.length > 1) td.replaceChildren(h("span", { class: "cell" }, ...td.childNodes)); // keep "value · date" together when rows stack
    }));
    return h("div", { class: "tablewrap " + (cls || "stack-sm") }, h("table", {}, h("thead", {}, h("tr", {}, ths)), h("tbody", {}, rows)));
  }
  const th = (label, tip) => [label, tip ? hint(tip) : null];
  const pctCell = (v, d = 2) => h("td", {}, num(pct(v, d), v == null ? "" : dir(v) === "up" ? "up-t" : dir(v) === "down" ? "down-t" : ""));

  function renderDetails() {
    const d = state.data, L = t(), body = $("details-body"), act = active();
    const parts = [];

    // all numbers
    const keys = act.map((s) => keyOf(s.id)).concat(["gold_oz_usd", "silver_oz_usd"]).filter(asset);
    const slotColor = (key) => { const s = SERIES.find((x) => keyOf(x.id) === key); return s ? color(s.slot) : cssVar("--ink-3"); };
    const label = (a) => (a.key === "gold_oz_usd" ? L.goldGlobal : a.key === "silver_oz_usd" ? L.silverGlobal : nameOf(a.group === "currency" ? a.key : a.group));
    const short = (dstr) => fmtDate(dstr, false);
    const monthCell = (m) => (m ? [fmtMonth(m.month) + " ", num(pct(m.change_pct))] : "–");
    const glossary = h("dl", { class: "glossary" }, [["colYtd", "ytd"], ["col1d", "d1"], ["col7d", "d7"], ["col30d", "d30"], ["colHigh", "high"], ["colLow", "low"],
      ["colAvg", "avg"], ["colVol", "vol"], ["colDd", "dd"], ["colBest", "best"], ["colWorst", "worst"]].map(([c, k]) => [h("dt", {}, L[c]), h("dd", {}, L.tips[k])]));
    parts.push(h("h3", {}, L.hKpi), h("p", { class: "lead lead-wide" }, L.leadKpi), h("p", { class: "lead lead-narrow" }, L.leadKpiNarrow), table(
      [L.colAsset, L.colLatest, th(L.colYtd, L.tips.ytd), th(L.col1d, L.tips.d1), th(L.col7d, L.tips.d7), th(L.col30d, L.tips.d30),
       th(L.colHigh, L.tips.high), th(L.colLow, L.tips.low), th(L.colAvg, L.tips.avg), th(L.colVol, L.tips.vol), th(L.colDd, L.tips.dd),
       th(L.colBest, L.tips.best), th(L.colWorst, L.tips.worst)],
      keys.map((key) => { const a = asset(key), k = a.kpis;
        return h("tr", {}, h("td", {}, h("span", { class: "dot", style: "--c:" + slotColor(key) }), label(a)),
          h("td", {}, num(nf(k.end, a.decimals))), pctCell(k.change_pct), pctCell(k.change_1d_pct), pctCell(k.change_7d_pct), pctCell(k.change_30d_pct),
          h("td", {}, num(nf(k.high, a.decimals)), " · " + short(k.high_date)), h("td", {}, num(nf(k.low, a.decimals)), " · " + short(k.low_date)),
          h("td", {}, num(nf(k.average, a.decimals))), h("td", {}, num(k.daily_volatility_pct == null ? "–" : nf(k.daily_volatility_pct, 2) + "%")),
          h("td", {}, num(pct(k.max_drawdown_pct))), h("td", {}, monthCell(k.best_month)), h("td", {}, monthCell(k.worst_month))); }), "stack-md"), glossary);

    // month by month
    const months = asset(keyOf(act[0].id)).kpis.monthly;
    parts.push(h("h3", {}, L.hMonth), table(
      [L.colMonth].concat(act.map((s) => [h("span", { class: "dot", style: "--c:" + color(s.slot) }), nameOf(s.id)])),
      months.map((mo) => h("tr", {}, h("td", {}, fmtMonth(mo.month, true) + (mo.partial ? " (" + L.soFar + ")" : "")),
        act.map((s) => { const r = asset(keyOf(s.id)).kpis.monthly.find((x) => x.month === mo.month); return pctCell(r ? r.change_pct : null); })))
        .concat([h("tr", { class: "total" }, h("td", {}, L.wholePeriod), act.map((s) => pctCell(asset(keyOf(s.id)).kpis.change_pct)))])));

    // drivers
    const drv = act.filter((s) => s.id !== "usd" && asset(keyOf(s.id)).drivers);
    if (drv.length) {
      parts.push(h("h3", {}, L.hDrivers), h("p", { class: "lead" }, L.leadDrivers), table(
        [L.colAsset, L.colInEgp, "=  " + L.colGlobal, "×  " + L.colFx],
        drv.map((s) => { const a = asset(keyOf(s.id)), dr = a.drivers;
          return h("tr", {}, h("td", {}, nameOf(s.id)), pctCell(a.kpis.change_pct),
            h("td", {}, L.driverBase[s.id] + "  ", num(pct(dr.base_pct, 2))), h("td", {}, num(pct(dr.fx_pct, 2)))); })));
    }

    // local gold shops
    parts.push(h("h3", {}, L.hLocal), h("p", { class: "lead" }, L.leadLocal));
    const l = d.local;
    if (!l || l.error || !l.rows) parts.push(h("p", { class: "lead" }, L.localError));
    else {
      parts.push(table([L.colKarat, L.colSell, L.colBuy, L.colImplied, L.colGap],
        l.rows.map((r) => h("tr", {}, h("td", {}, num(String(r.karat))), h("td", {}, num(nf(r.sell, 0))), h("td", {}, num(nf(r.buy, 0))),
          h("td", {}, num(nf(r.derived, 0))), h("td", {}, num(pct(r.gap_pct, 2)), r.suspect ? " ⚠" : "")))));
      parts.push(h("p", { class: "lead" }, L.localSource(l.source, fmtTime(l.fetched_at)) + (l.stale ? L.localStale : "")));
    }

    // daily data (lazy)
    const g = d.grid;
    const cols = ["usd", "eur", "gbp", "gold_24", "gold_21", "gold_18", "silver", "gold_oz_usd", "silver_oz_usd"].filter((k) => g.series[k] && asset(k));
    const colName = (k) => ({ gold_24: L.names.gold(24), gold_21: L.names.gold(21), gold_18: L.names.gold(18), gold_oz_usd: L.goldGlobal, silver_oz_usd: L.silverGlobal })[k] || L.names[k];
    const dataBox = h("div");
    const showBtn = h("button", { type: "button", class: "show-data" }, L.showData);
    showBtn.addEventListener("click", () => {
      showBtn.remove();
      dataBox.append(table([L.colDate].concat(cols.map(colName)),
        g.dates.map((dd, i) => h("tr", {}, h("td", {}, num(dd)), cols.map((k) => h("td", {}, num(nf(g.series[k][i], asset(k).decimals)))))).reverse(), "datatable stack-md"));
    });
    parts.push(h("h3", {}, L.hData), showBtn, dataBox);

    // how + sources
    parts.push(h("h3", {}, L.hHow), h("ul", { class: "lead" }, L.how.map((x) => h("li", {}, x))));
    parts.push(h("h3", {}, L.hSources), h("ul", { class: "lead" },
      Object.keys(d.sources).map((sym) => h("li", {}, L.sourceLine(state.lang === "ar" ? SYMBOL_AR[sym] || sym : d.labels[sym], L.sourceNames[d.sources[sym]] || d.sources[sym]))),
      h("li", {}, L.localLine(l && l.source)), h("li", {}, L.liveLine)));
    body.replaceChildren(...parts);
  }

  // ------------------------------------------------------------------ "updated 5 min ago" + quiet auto-refresh
  function updateAgo() {
    const d = state.data;
    if (!d) return;
    const mins = Math.max(0, Math.floor((Date.now() - new Date(d.fetched_at).getTime()) / 60000));
    const sub = $("subtitle");
    sub.textContent = t().subtitle(fmtDate(d.period.start), fmtDate(d.period.end), t().ago(mins));
    sub.title = fmtTime(d.fetched_at);
  }
  let lastAuto = 0;
  function maybeRefresh() { // the server re-downloads only when its data is older than 30 minutes
    if (!state.data || state.loading || document.hidden) return;
    if (Date.now() - new Date(state.data.fetched_at).getTime() < 31 * 60000) return;
    if (Date.now() - lastAuto < 10 * 60000) return; // offline: don't retry more than every 10 minutes
    lastAuto = Date.now();
    load(false, true);
  }

  // ------------------------------------------------------------------ insights: plain-language facts
  const ICONS = {
    peak: "M3 19l6-9 4 5 3-4 5 8z",
    streak: "M4 16l5-5 4 4 7-7M15 8h5v5",
    jumpy: "M3 12l3-6 4 12 4-12 4 12 3-6",
    calm: "M3 12c3-3 6 3 9 0s6-3 9 0",
    month: "M4 6h16v14H4zM4 10h16M9 3v4M15 3v4",
  };
  function icon(name) {
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 24 24"); svg.setAttribute("aria-hidden", "true"); svg.setAttribute("class", "ico");
    const path = document.createElementNS(svg.namespaceURI, "path");
    path.setAttribute("d", ICONS[name]);
    svg.append(path);
    return svg;
  }
  function streakOf(vals) { // consecutive moves in the same direction up to the latest day (flat days skipped)
    let dirn = 0, n = 0;
    for (let i = vals.length - 1; i > 0; i--) {
      const a = vals[i], b = vals[i - 1];
      if (a == null || b == null) break;
      if (a === b) continue;
      const d = a > b ? 1 : -1;
      if (!dirn) dirn = d; else if (d !== dirn) break;
      n++;
    }
    return { dirn, n };
  }
  function renderInsights() {
    const L = t().insights, act = active(), out = [];
    const b = (id) => h("b", {}, nameOf(id));
    const rows = act.map((s) => ({ id: s.id, a: asset(keyOf(s.id)), k: asset(keyOf(s.id)).kpis }));
    const enough = rows.filter((r) => r.k.n_days >= 5);
    const top = enough.find((r) => r.k.end >= r.k.high * 0.999);
    const bottom = enough.find((r) => r.k.end <= r.k.low * 1.001);
    if (top) out.push({ icon: "peak", parts: L.atHigh(b(top.id)) });
    else if (bottom) out.push({ icon: "peak", parts: L.atLow(b(bottom.id)) });
    const gold = enough.find((r) => r.id === "gold");
    if (gold && gold !== top && gold.k.end / gold.k.high - 1 <= -0.03) {
      out.push({ icon: "peak", parts: L.fromPeak(b("gold"), num(nf(gold.k.high, 0) + " " + t().live.g), fmtDate(gold.k.high_date, false),
        num(pct(Math.abs((gold.k.end / gold.k.high - 1) * 100)).slice(1))) });
    }
    const streaks = rows.map((r) => Object.assign({ id: r.id }, streakOf(state.data.grid.series[r.a.key]))).sort((x, y) => y.n - x.n);
    if (streaks.length && streaks[0].n >= 3) out.push({ icon: "streak", parts: (streaks[0].dirn > 0 ? L.streakUp : L.streakDown)(b(streaks[0].id), num(String(streaks[0].n))) });
    const vol = rows.filter((r) => r.k.daily_volatility_pct != null).sort((x, y) => y.k.daily_volatility_pct - x.k.daily_volatility_pct);
    if (vol.length > 1) {
      out.push({ icon: "jumpy", parts: L.jumpy(b(vol[0].id), num(nf(vol[0].k.daily_volatility_pct, 1) + "%")) });
      out.push({ icon: "calm", parts: L.calm(b(vol[vol.length - 1].id), num(nf(vol[vol.length - 1].k.daily_volatility_pct, 1) + "%")) });
    }
    const best = rows.filter((r) => r.k.best_month).sort((x, y) => y.k.best_month.change_pct - x.k.best_month.change_pct)[0];
    if (best && best.k.best_month.change_pct > 0) out.push({ icon: "month", parts: L.bestMonth(b(best.id), fmtMonth(best.k.best_month.month, true), num(pct(best.k.best_month.change_pct))) });
    const box = $("insights");
    box.replaceChildren(...out.slice(0, 4).map((x, i) => h("div", { class: "insight", style: "--i:" + i }, h("span", { class: "insight-ico" }, icon(x.icon)), h("p", {}, ...x.parts))));
    box.hidden = !out.length;
  }

  // ------------------------------------------------------------------ calculator: "how much is it worth?" / "what does my budget buy?"
  function unitPrice(item, which) { // EGP per unit at the latest price ("end") or on 31 Dec ("start")
    const k = (key) => (asset(key) ? asset(key).kpis[which] : null);
    if (item === "pound") return k("gold_21") == null ? null : k("gold_21") * 8;
    return k(item);
  }
  function shopPrices() { // {karat: {sell, buy}}: the freshest Egyptian shop prices we have
    const live = state.live && state.live.local && state.live.local.karats;
    if (live) {
      const out = {};
      Object.keys(live).forEach((kt) => { out[Number(kt)] = live[kt]; });
      return out;
    }
    const rows = state.data && state.data.local && state.data.local.rows;
    const out = {};
    (rows || []).filter((r) => !r.suspect).forEach((r) => { out[r.karat] = r; });
    return out;
  }
  function shopBuy(item) {
    const karat = item === "pound" ? 21 : item.indexOf("gold_") === 0 ? Number(item.slice(5)) : null;
    const p = karat && shopPrices()[karat];
    return p && p.buy ? p.buy * (item === "pound" ? 8 : 1) : null;
  }
  function amountInput(id, value, label, onInput) {
    const input = h("input", { id, type: "text", inputmode: "decimal", autocomplete: "off", dir: "ltr", value, "aria-label": label });
    input.addEventListener("input", onInput);
    return h("label", { class: "field" }, h("span", {}, label), input);
  }
  function renderCalc() {
    const L = t().calc, box = $("calc");
    const seg = h("div", { class: "seg", role: "group", "aria-label": L.title },
      ["have", "spend"].map((m) => {
        const btn = h("button", { type: "button", "aria-pressed": String(state.calcMode === m) }, L[m]);
        btn.addEventListener("click", () => { state.calcMode = m; store.set("calcMode", m); renderCalc(); });
        return btn;
      }));
    const out = h("div", { class: "calc-out", "aria-live": "polite" });
    let form;
    if (state.calcMode === "have") {
      const sel = h("select", { id: "calc-item", "aria-label": L.items[state.calcItem] },
        CALC_ITEMS.filter((it) => unitPrice(it, "end") != null).map((it) => h("option", { value: it, selected: it === state.calcItem }, L.items[it])));
      sel.addEventListener("change", () => { state.calcItem = sel.value; store.set("calcItem", sel.value); updateCalc(); });
      form = h("div", { class: "calc-form" },
        amountInput("calc-amount", state.calcAmount, L.amount, (e) => { state.calcAmount = e.target.value; store.set("calcAmount", e.target.value); updateCalc(); }),
        h("label", { class: "field grow" }, h("span", { "aria-hidden": "true" }, " "), sel));
    } else {
      form = h("div", { class: "calc-form" },
        amountInput("calc-budget", state.budget, L.budget, (e) => { state.budget = e.target.value; store.set("budget", e.target.value); updateCalc(); }));
    }
    box.replaceChildren(h("div", { class: "tool-head" }, h("h2", {}, L.title), seg), form, out, h("p", { class: "tool-note" }, L.note));
    updateCalc();
  }
  function updateCalc() {
    const L = t().calc, out = document.querySelector("#calc .calc-out");
    if (!out) return;
    if (state.calcMode === "have") {
      const qty = parseAmount(state.calcAmount), item = state.calcItem;
      const now = unitPrice(item, "end"), then = unitPrice(item, "start"), shop = shopBuy(item);
      if (qty == null || now == null) { out.replaceChildren(h("p", { class: "calc-big" }, "–")); return; }
      const v = qty * now, v0 = then == null ? null : qty * then;
      const lines = [h("span", { class: "calc-label" }, L.worth), h("p", { class: "calc-big" }, num(nf(v, v >= 100 ? 0 : 2)), " ", h("small", {}, L.egp))];
      if (shop != null) lines.push(h("p", { class: "calc-line" }, L.shopBuys + " ", h("b", {}, num(nf(qty * shop, 0))), " " + L.egp));
      if (v0 != null) {
        const diff = v - v0;
        lines.push(h("p", { class: "calc-line" }, L.onBase(baseDate()) + " ", num(nf(v0, v0 >= 100 ? 0 : 2)), " " + L.egp + " · ",
          h("b", { class: diff >= 0 ? "up-t" : "down-t" }, num((diff >= 0 ? "+" : "−") + nf(Math.abs(diff), Math.abs(diff) >= 100 ? 0 : 2))), " ",
          pill(asset(item === "pound" ? "gold_21" : item).kpis.change_pct)));
      }
      out.replaceChildren(...lines);
    } else {
      const budget = parseAmount(state.budget);
      if (budget == null) { out.replaceChildren(h("p", { class: "calc-big" }, "–")); return; }
      const items = ["gold_" + state.karat, "pound", "silver", "usd", "eur", "gbp"].filter((it) => unitPrice(it, "end"));
      out.replaceChildren(h("span", { class: "calc-label" }, L.budgetLead),
        h("ul", { class: "buys" }, items.map((it) => h("li", {}, h("b", {}, num(nf(budget / unitPrice(it, "end"), 2))), h("span", {}, L.items[it])))));
    }
  }

  // ------------------------------------------------------------------ what if: the year in money, not percentages
  function renderWhatIf() {
    const L = t().whatif, box = $("whatif");
    box.replaceChildren(h("div", { class: "tool-head" }, h("h2", {}, L.title)),
      h("div", { class: "calc-form" }, amountInput("whatif-amount", state.whatif, L.amount, (e) => { state.whatif = e.target.value; store.set("whatif", e.target.value); updateWhatIf(); })),
      h("p", { class: "tool-note lead-in" }, L.lead(baseDate())),
      h("div", { class: "wif", "aria-live": "polite" }));
    updateWhatIf();
  }
  function updateWhatIf() {
    const L = t().whatif, list = document.querySelector("#whatif .wif");
    if (!list) return;
    const amt = parseAmount(state.whatif);
    if (!amt) { list.replaceChildren(); return; }
    const rows = active().map((s) => { const k = asset(keyOf(s.id)).kpis; return { name: nameOf(s.id), c: color(s.slot), v: (amt * k.end) / k.start, p: k.change_pct }; });
    rows.push({ name: L.cash, c: cssVar("--ink-3"), v: amt, p: 0, cash: true });
    rows.sort((x, y) => y.v - x.v);
    const max = Math.max.apply(null, rows.map((r) => r.v));
    list.replaceChildren(...rows.map((r) => h("div", { class: "wif-row" + (r.cash ? " cash" : ""), style: "--c:" + r.c },
      h("span", { class: "wif-name" }, h("i"), r.name),
      h("span", { class: "wif-bar" }, h("span", { class: "wif-fill", style: "width:" + ((r.v / max) * 100).toFixed(1) + "%" }),
        h("span", { class: "wif-base", style: "inset-inline-start:" + ((amt / max) * 100).toFixed(1) + "%" })),
      h("span", { class: "wif-val" }, num(nf(r.v, 0)), r.cash ? null : pill(r.p)))));
  }

  // ------------------------------------------------------------------ live strip: real-time gold and silver while the page is open
  const lastLive = {};
  async function pollLive() {
    if (document.hidden) return;
    try {
      const res = await fetch("/api/live");
      if (res.ok) state.live = await res.json();
    } catch (e) { /* keep the last values */ }
    renderLive();
    updateCalc();
  }
  function renderLive() {
    const box = $("live"), lv = state.live, L = t().live;
    // Only show the strip when real-time prices actually arrived (not just cached shop prices).
    if (!lv || !state.data || !lv.metals || !Object.keys(lv.metals).length) { box.hidden = true; return; }
    const items = [];
    const change = (now, ref) => (ref ? (now / ref - 1) * 100 : null);
    const toNum = (x) => parseFloat(String(x).replace(/,/g, ""));
    const item = (key, label, value, unit, chg) => {
      const val = num(value, "live-val");
      if (lastLive[key] != null && lastLive[key] !== value) val.classList.add(toNum(value) > toNum(lastLive[key]) ? "flash-up" : "flash-down");
      lastLive[key] = value;
      return h("div", { class: "live-item" }, h("span", { class: "live-label" }, label),
        h("span", { class: "live-row" }, val, h("span", { class: "live-unit" }, unit),
          chg == null ? null : h("span", { class: "live-chg " + dir(chg) }, num(pct(chg, 2)), " " + L.today)));
    };
    const xau = lv.metals && lv.metals.XAU, xag = lv.metals && lv.metals.XAG;
    if (xau) items.push(item("xau", L.gold, nf(xau.usd_oz, 2), L.oz, change(xau.usd_oz, xau.ref)));
    if (xag) items.push(item("xag", L.silver, nf(xag.usd_oz, 2), L.oz, change(xag.usd_oz, xag.ref)));
    if (xau && lv.fx) items.push(item("gegp" + state.karat, L.goldEgp(state.karat), nf(((xau.usd_oz * lv.fx) / OUNCE_G) * Number(state.karat) / 24, 0), L.g, change(xau.usd_oz, xau.ref)));
    const shop = shopPrices()[Number(state.karat)];
    if (shop) items.push(h("div", { class: "live-item" }, h("span", { class: "live-label" }, L.shop(state.karat)),
      h("span", { class: "live-row" }, h("span", { class: "live-unit" }, L.sells), num(nf(shop.sell, 0), "live-val"),
        h("span", { class: "live-unit" }, "· " + L.buys), num(nf(shop.buy, 0), "live-val"))));
    if (!items.length) { box.hidden = true; return; }
    const stamp = xau && xau.updated_at ? new Date(xau.updated_at) : new Date(lv.fetched_at);
    const hhmm = String(stamp.getHours()).padStart(2, "0") + ":" + String(stamp.getMinutes()).padStart(2, "0");
    box.replaceChildren(h("div", { class: "live-tag" }, h("i", { class: "live-dot" }), h("b", {}, L.tag), hint(L.info), h("span", { class: "live-time" }, num(L.at(hhmm)))), ...items);
    box.hidden = false;
  }

  // ------------------------------------------------------------------ save the chart as an image
  function saveChart() {
    const c = state.chart;
    if (!c) return;
    const src = c.canvas, T = theme(), ratio = src.width / (src.clientWidth || src.width) || 1;
    const sets = c.data.datasets.filter((ds, i) => c.isDatasetVisible(i));
    const legend = sets.length > 1; // the colour chips are outside the chart, so draw a legend into the image
    const pad = Math.round(18 * ratio), head = Math.round((legend ? 84 : 58) * ratio);
    const out = document.createElement("canvas");
    out.width = src.width + pad * 2; out.height = src.height + head + pad;
    const x = out.getContext("2d");
    x.fillStyle = T.surfaceSolid; x.fillRect(0, 0, out.width, out.height);
    x.direction = isRtl() ? "rtl" : "ltr"; x.textAlign = isRtl() ? "right" : "left";
    const tx = isRtl() ? out.width - pad : pad, d = state.data;
    const title = state.tab === "price" ? nameOf(state.focus) + " · " + t().units[state.focus] : state.tab === "compare" ? t().tabCompare : t().tabMonth;
    x.fillStyle = T.ink; x.font = "700 " + Math.round(17 * ratio) + "px -apple-system, Segoe UI, Roboto, sans-serif";
    x.fillText(title, tx, pad + Math.round(18 * ratio));
    x.fillStyle = T.ink3; x.font = Math.round(12 * ratio) + "px -apple-system, Segoe UI, Roboto, sans-serif";
    x.fillText(t().title + " · " + fmtDate(d.period.base_date) + " – " + fmtDate(d.period.end), tx, pad + Math.round(40 * ratio));
    if (legend) {
      x.font = "600 " + Math.round(12 * ratio) + "px -apple-system, Segoe UI, Roboto, sans-serif";
      let lx = tx;
      const ly = pad + Math.round(64 * ratio), sw = Math.round(14 * ratio), gap = Math.round(6 * ratio), space = Math.round(18 * ratio);
      sets.forEach((ds) => {
        const w = x.measureText(ds.label).width;
        const colour = typeof ds.borderColor === "string" && ds.type !== "bar" && c.config.type === "line" ? ds.borderColor : ds.backgroundColor;
        x.fillStyle = colour;
        const sx = isRtl() ? lx - sw : lx;
        x.fillRect(sx, ly - Math.round(5 * ratio), sw, Math.round(c.config.type === "line" ? 3 * ratio : 10 * ratio));
        x.fillStyle = T.ink2;
        x.fillText(ds.label, isRtl() ? lx - sw - gap : lx + sw + gap, ly + Math.round(3 * ratio));
        lx += (isRtl() ? -1 : 1) * (sw + gap + w + space);
      });
    }
    x.drawImage(src, pad, head);
    out.toBlob((blob) => {
      if (!blob) return;
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = "nabd-" + (state.tab === "price" ? keyOf(state.focus) : state.tab) + "-" + d.period.end + ".png";
      document.body.append(a); a.click(); a.remove();
      setTimeout(() => URL.revokeObjectURL(a.href), 4000);
    }, "image/png");
  }

  // Re-measure the chart whenever its box may have changed. Chart.js does this itself in most browsers,
  // but Safari could keep the size measured while the page was still being laid out or in a background tab.
  function fitChart() {
    const c = state.chart, box = document.querySelector(".chart");
    if (!c || !box) return;
    const w = box.clientWidth, hgt = box.clientHeight;
    if (w && hgt && (Math.abs(c.width - w) > 1 || Math.abs(c.height - hgt) > 1)) c.resize(w, hgt);
  }
  if (window.ResizeObserver) new ResizeObserver(() => requestAnimationFrame(fitChart)).observe(document.querySelector(".chart"));
  window.addEventListener("resize", fitChart);
  window.addEventListener("pageshow", fitChart);
  document.addEventListener("visibilitychange", () => { if (!document.hidden) fitChart(); });

  // ------------------------------------------------------------------ ⓘ explanations: one floating bubble, never clipped
  const tipBox = h("div", { class: "tipbox", role: "tooltip", id: "tipbox", hidden: true });
  document.body.append(tipBox);
  let tipFor = null, tipAt = 0;
  function showTip(el) {
    if (tipFor !== el) tipAt = Date.now();
    tipFor = el;
    tipBox.textContent = el.getAttribute("data-tip");
    tipBox.hidden = false;
    const r = el.getBoundingClientRect(), w = tipBox.offsetWidth, ht = tipBox.offsetHeight, vw = document.documentElement.clientWidth;
    const x = Math.max(8, Math.min(r.left + r.width / 2 - w / 2, vw - w - 8));
    const y = r.top - ht - 8 >= 8 ? r.top - ht - 8 : r.bottom + 8;
    tipBox.style.left = x + "px";
    tipBox.style.top = y + "px";
    el.setAttribute("aria-describedby", "tipbox");
  }
  function hideTip() { if (tipFor) tipFor.removeAttribute("aria-describedby"); tipFor = null; tipBox.hidden = true; }
  document.addEventListener("mouseover", (e) => { const el = e.target.closest && e.target.closest(".hint"); if (el) showTip(el); });
  document.addEventListener("mouseout", (e) => { if (e.target.closest && e.target.closest(".hint")) hideTip(); });
  document.addEventListener("focusin", (e) => { if (e.target.classList && e.target.classList.contains("hint")) showTip(e.target); });
  document.addEventListener("focusout", (e) => { if (e.target.classList && e.target.classList.contains("hint")) hideTip(); });
  document.addEventListener("click", (e) => { // tap support on touch screens
    const el = e.target.closest && e.target.closest(".hint");
    if (el) { if (tipFor === el && Date.now() - tipAt > 400) hideTip(); else showTip(el); } else hideTip(); // a tap also fires a hover first
  });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") hideTip(); });
  window.addEventListener("scroll", () => { if (tipFor) showTip(tipFor); }, { passive: true }); // follow the ⓘ while scrolling

  // ------------------------------------------------------------------ wiring
  document.querySelectorAll("[data-lang]").forEach((b) => b.addEventListener("click", () => {
    state.lang = b.dataset.lang; store.set("lang", state.lang); applyLang(); render();
  }));
  $("theme").addEventListener("click", () => {
    const order = ["auto", "light", "dark"];
    state.theme = order[(order.indexOf(state.theme) + 1) % 3]; store.set("theme", state.theme); applyTheme(); applyLang(); render();
  });
  document.querySelectorAll("#tabs [data-tab]").forEach((b) => b.addEventListener("click", () => {
    state.tab = b.dataset.tab; store.set("tab", state.tab); syncCards(); renderTabs(); renderChart();
  }));
  $("karat").addEventListener("change", (e) => { state.karat = e.target.value; store.set("karat", state.karat); render(); });
  $("details").addEventListener("toggle", () => { if ($("details").open) renderDetails(); });
  $("refresh").addEventListener("click", () => load(true));
  $("save-chart").addEventListener("click", saveChart);
  setInterval(() => { updateAgo(); maybeRefresh(); }, 30000);
  setInterval(pollLive, 60000);
  document.addEventListener("visibilitychange", () => { if (!document.hidden) { updateAgo(); maybeRefresh(); pollLive(); } });
  const mq = window.matchMedia("(prefers-color-scheme: dark)");
  (mq.addEventListener ? mq.addEventListener.bind(mq, "change") : mq.addListener.bind(mq))(() => { if (state.theme === "auto") render(); });

  if (!["price", "compare", "month"].includes(state.tab)) state.tab = "price";
  $("karat").value = state.karat;
  applyTheme();
  applyLang();
  load(false);
})();
