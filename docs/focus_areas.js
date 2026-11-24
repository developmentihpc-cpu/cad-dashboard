/* focus_areas.js — sub-national "focus areas" added to a country's report (English + Arabic).
 * A focus area is marked on the report's country map and gets two slides after the sector slides:
 *   1 · overview — area map, key facts, what the area is, and recent announcements
 *   2 · sectors and priority needs — key sectors as bullets, then where support is needed
 * Content is researched and dated (asOf): review it when the sources update. `dhs` names the area as it
 * appears in data/subnational/{ISO3}.json (survey figures cited in the text come from there).
 * Every text is [English, Arabic]; a sector or announcement is [[heading EN, AR], [text EN, AR]].
 */
'use strict';
const FOCUS_AREAS = {
  Jordan: [{
    key: 'aqaba',
    name: ['Al Aqabah', 'العقبة'],
    ll: [29.532, 35.006],                       // Aqaba city
    dhs: 'Aqaba',                               // governorate name in the DHS survey file
    asOf: '2026-11',
    tagline: ["Jordan's gateway to the Red Sea", 'بوابة الأردن على البحر الأحمر'],
    facts: [
      ['188,160', ['Population (2015 census)', 'عدد السكان (تعداد 2015)'], ['Aqaba governorate · new census due 2026', 'محافظة العقبة · تعداد جديد في 2026']],
      ['17.3%', ['Unemployment, 2024', 'معدل البطالة، 2024'], ['Lowest of the 12 governorates (national 21.4%)', 'الأدنى بين المحافظات الاثنتي عشرة (الوطني 21.4%)']],
      [['1.0M TEU', '1.0 مليون حاوية'], ['Containers handled, 2025', 'الحاويات المناولة، 2025'],
       ['TEU = twenty-foot equivalent unit, the standard container size · up 22% on 2024', 'وحدة مكافئة لحاوية بطول عشرين قدماً · بزيادة 22% عن 2024']],
      ['61,000', ['Jobs in the economic zone', 'الوظائف في المنطقة الاقتصادية'], ['ASEZA, 2025 · 10,000+ private-sector jobs since 2018', 'سلطة المنطقة، 2025 · أكثر من 10,000 وظيفة في القطاع الخاص منذ 2018']],
    ],
    overview: [
      ["Jordan's only seaport and its gateway to the Red Sea, carrying most of the country's sea trade and transit cargo for Iraq and, increasingly, Syria.",
       'الميناء البحري الوحيد في الأردن وبوابته على البحر الأحمر، ويتولى معظم تجارة المملكة البحرية وبضائع الترانزيت المتجهة إلى العراق، وبصورة متزايدة إلى سوريا.'],
      ['A special economic zone since 2001 (ASEZA), with tax and customs incentives; priority sectors are industry, IT and tourism, anchored by the Aqaba–Petra–Wadi Rum "Golden Triangle".',
       'منطقة اقتصادية خاصة منذ عام 2001 تديرها سلطة منطقة العقبة الاقتصادية الخاصة، مع حوافز ضريبية وجمركية؛ وقطاعاتها ذات الأولوية الصناعة وتقنية المعلومات والسياحة، ومحورها «المثلث الذهبي» (العقبة والبتراء ووادي رم).'],
      ["Key to solving Jordan's water scarcity: the Aqaba–Amman Water Desalination and Conveyance Project (National Water Carrier) will desalinate 300 million m³ a year at Aqaba — about 40% of the Kingdom's drinking water. Ground was broken in Aqaba on 18 November 2026; operations are due in late 2030.",
       'ركيزة لمعالجة شحّ المياه في الأردن: سيُحلّي مشروع ناقل المياه الوطني (العقبة–عمّان) 300 مليون متر مكعب سنوياً في العقبة، أي نحو 40% من مياه الشرب في المملكة. ووُضع حجر الأساس في العقبة في 18 نوفمبر 2026، ويُتوقع بدء التشغيل في أواخر 2030.'],
    ],
    news: [   // 2026 announcements involving Aqaba and Jordan's partners
      [['Jordan–EU Investment Conference, 19 Nov 2026', 'مؤتمر الاستثمار الأردني–الأوروبي، 19 نوفمبر 2026'],
       ['Aqaba Digital Hub joins the EBRD Blue Ribbon programme (€12 million loan, €3 million EU guarantee); EU backing to extend the Medusa submarine cable to Jordan.',
        'انضمام مركز العقبة الرقمي إلى برنامج «الشريط الأزرق» للبنك الأوروبي لإعادة الإعمار والتنمية (قرض 12 مليون يورو وضمان أوروبي 3 ملايين يورو)؛ ودعم أوروبي لمدّ كابل «ميدوسا» البحري إلى الأردن.']],
      [['UAE–Jordan Aqaba railway, 15 Apr 2026', 'سكة حديد العقبة بين الإمارات والأردن، 15 أبريل 2026'],
       ['About US$2.3 billion joint investment in a 360 km line from Aqaba port to the phosphate and potash mines (16 million tonnes a year).',
        'استثمار مشترك بنحو 2.3 مليار دولار في خط بطول 360 كم يربط ميناء العقبة بمناجم الفوسفات والبوتاس، بطاقة 16 مليون طن سنوياً.']],
      [['AD Ports Group concession, 5 Feb 2026', 'امتياز مجموعة موانئ أبوظبي، 5 فبراير 2026'],
       ['30-year concession to run the Aqaba Multipurpose Port (70/30 joint venture with the Aqaba Development Corporation), operating from August 2026.',
        'امتياز لمدة 30 عاماً لتشغيل ميناء العقبة متعدد الأغراض (مشروع مشترك مع شركة تطوير العقبة بنسبة 70/30)، يبدأ تشغيله في أغسطس 2026.']],
      [['Jordan–Saudi economic zones MoU, Apr 2026', 'مذكرة تفاهم أردنية–سعودية للمناطق الاقتصادية، أبريل 2026'],
       ["Agreement to develop economic zones together; Saudi Arabia was Jordan's largest investor in 2025.",
        'اتفاق على تطوير مناطق اقتصادية مشتركة؛ وكانت السعودية أكبر مستثمر في الأردن عام 2025.']],
    ],
    sectors: [
      [['Ports & logistics', 'الموانئ والخدمات اللوجستية'],
       ['Record 2025: 1.0 million TEU of containers (+22%), 15.0 million tonnes of dry bulk and 6.2 million tonnes of liquid bulk; new UAE-backed port and rail investment.',
        'عام قياسي في 2025: مليون حاوية نمطية (بزيادة 22%)، و15.0 مليون طن من السوائب الجافة، و6.2 مليون طن من السوائب السائلة؛ مع استثمارات إماراتية جديدة في الميناء وسكة الحديد.']],
      [['Water', 'المياه'],
       ['Hosts the National Water Carrier: 250 million m³ a year for Amman and 50 million for Aqaba, partly solar-powered (281 MW).',
        'تحتضن ناقل المياه الوطني: 250 مليون متر مكعب سنوياً لعمّان و50 مليوناً للعقبة، يعمل جزئياً بالطاقة الشمسية (281 ميغاواط).']],
      [['Tourism', 'السياحة'],
       ['Red Sea coast, diving and Wadi Rum (about 300,000 visitors in 2025); visitor numbers are sensitive to regional conflict.',
        'ساحل البحر الأحمر والغوص ووادي رم (نحو 300,000 زائر في 2025)؛ وتتأثر أعداد الزوار بالنزاعات الإقليمية.']],
      [['Digital', 'الاقتصاد الرقمي'],
       ['The Aqaba Digital Hub (data centre and connectivity) is expanding with EBRD and EU support.',
        'يتوسع مركز العقبة الرقمي (مركز بيانات واتصال) بدعم من البنك الأوروبي لإعادة الإعمار والتنمية والاتحاد الأوروبي.']],
      [['Jobs', 'فرص العمل'],
       ['Unemployment of 17.3% (2024) is the lowest in Jordan but still high, and higher among women and young people.',
        'تبلغ البطالة 17.3% (2024)، وهي الأدنى في الأردن لكنها لا تزال مرتفعة، وترتفع أكثر بين النساء والشباب.']],
    ],
    needs: [
      ['Child immunisation: 84% of children have all basic vaccinations, against 92% nationally — the third-lowest of the 12 governorates (2023). Outreach to mobile and migrant-worker families and remote desert communities (Wadi Rum, Al Quwayrah).',
       'تحصين الأطفال: 84% من الأطفال تلقّوا جميع اللقاحات الأساسية مقابل 92% على المستوى الوطني، وهي ثالث أدنى نسبة بين المحافظات الاثنتي عشرة (2023). ويُوصى بالوصول إلى الأسر المتنقلة وأسر العمال الوافدين والمجتمعات الصحراوية النائية (وادي رم والقويرة).'],
      ['Skills for the new investment: technical and vocational training linked to employers in ports, rail, logistics, tourism and digital services, with places reserved for young people and women.',
       'المهارات لخدمة الاستثمارات الجديدة: تدريب تقني ومهني مرتبط بأصحاب العمل في الموانئ وسكك الحديد والخدمات اللوجستية والسياحة والخدمات الرقمية، مع تخصيص مقاعد للشباب والنساء.'],
      ["Water and coast: one in four people in Aqaba lacked enough drinking water in the past month (2023) — secure local supply until the National Water Carrier opens, and protect the Gulf of Aqaba's coral reefs as desalination and port capacity expand.",
       'المياه والساحل: لم يحصل ربع سكان العقبة على مياه شرب كافية خلال الشهر الماضي (2023)؛ لذا يلزم تأمين الإمدادات المحلية حتى تشغيل ناقل المياه الوطني، وحماية الشعاب المرجانية في خليج العقبة مع توسع التحلية والموانئ.'],
      ['Tourism livelihoods: small-business finance and diversification for tour operators, desert camps and guides, so incomes withstand regional shocks.',
       'سبل العيش السياحية: تمويل المشروعات الصغيرة وتنويع الأنشطة لمنظمي الرحلات والمخيمات الصحراوية والأدلّاء، لتصمد الدخول أمام الصدمات الإقليمية.'],
    ],
    verdict: ["Al Aqabah is one of Jordan's better-performing governorates and a national growth hub — support should target the specific gaps below rather than broad-based need.",
              'تُعد العقبة من أفضل المحافظات أداءً في الأردن ومحركاً وطنياً للنمو؛ لذا ينبغي أن يستهدف الدعم الفجوات المحددة أدناه لا الاحتياجات العامة.'],
    sources: ['Jordan DoS · ASEZA · Jordan Shipping Association · AD Ports Group · EU/EBRD · Petra · DHS 2023',
              'الإحصاءات العامة · سلطة العقبة الاقتصادية · جمعية ملاحة الأردن · موانئ أبوظبي · الاتحاد الأوروبي · بترا · المسح الصحي 2023'],
  }],
};
if (typeof window !== 'undefined') window.FOCUS_AREAS = FOCUS_AREAS;
