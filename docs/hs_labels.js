/* hs_labels.js — short English and Arabic names for the 97 HS chapters (2-digit product groups) used in
 * data/trade_products.json, so the report can say "palm oil & fats" instead of the official HS wording.
 */
'use strict';
const HS2 = {
  '01':['Live animals','الحيوانات الحية'], '02':['Meat','اللحوم'], '03':['Fish & seafood','الأسماك والمأكولات البحرية'],
  '04':['Dairy, eggs & honey','الألبان والبيض والعسل'], '05':['Other animal products','منتجات حيوانية أخرى'], '06':['Live plants & flowers','النباتات الحية والزهور'],
  '07':['Vegetables','الخضروات'], '08':['Fruit & nuts','الفواكه والمكسرات'], '09':['Coffee, tea & spices','البن والشاي والتوابل'],
  '10':['Cereals','الحبوب'], '11':['Milled grains & flour','منتجات المطاحن والدقيق'], '12':['Oil seeds','البذور الزيتية'],
  '13':['Gums & resins','الصموغ والراتنجات'], '14':['Other vegetable products','منتجات نباتية أخرى'], '15':['Palm oil & other fats','زيت النخيل والدهون الأخرى'],
  '16':['Prepared meat & fish','اللحوم والأسماك المحضّرة'], '17':['Sugar','السكر'], '18':['Cocoa','الكاكاو'],
  '19':['Cereal & bakery products','منتجات الحبوب والمخابز'], '20':['Prepared vegetables & fruit','الخضروات والفواكه المحضّرة'], '21':['Other prepared foods','أغذية محضّرة أخرى'],
  '22':['Beverages','المشروبات'], '23':['Animal feed & food waste','الأعلاف وبقايا الصناعات الغذائية'], '24':['Tobacco','التبغ'],
  '25':['Salt, stone & cement','الملح والحجر والإسمنت'], '26':['Metal ores','خامات المعادن'], '27':['Oil, gas & coal','النفط والغاز والفحم'],
  '28':['Inorganic chemicals','الكيماويات غير العضوية'], '29':['Organic chemicals','الكيماويات العضوية'], '30':['Medicines','الأدوية'],
  '31':['Fertilisers','الأسمدة'], '32':['Dyes & paints','الأصباغ والدهانات'], '33':['Cosmetics & essential oils','مستحضرات التجميل والزيوت العطرية'],
  '34':['Soaps & detergents','الصابون والمنظفات'], '35':['Proteins, glues & enzymes','البروتينات والغراء والإنزيمات'], '36':['Explosives','المتفجرات'],
  '37':['Photographic goods','لوازم التصوير'], '38':['Other chemical products','منتجات كيميائية أخرى'], '39':['Plastics','اللدائن (البلاستيك)'],
  '40':['Rubber','المطاط'], '41':['Hides & skins','الجلود الخام'], '42':['Leather goods','المصنوعات الجلدية'],
  '43':['Furs','الفراء'], '44':['Wood','الخشب'], '45':['Cork','الفلين'],
  '46':['Basketware','منتجات القش والسلال'], '47':['Wood pulp','لب الخشب'], '48':['Paper & paperboard','الورق والكرتون'],
  '49':['Printed matter','المطبوعات'], '50':['Silk','الحرير'], '51':['Wool','الصوف'],
  '52':['Cotton','القطن'], '53':['Other vegetable fibres','ألياف نباتية أخرى'], '54':['Synthetic filaments','الشعيرات الاصطناعية'],
  '55':['Synthetic fibres','الألياف الاصطناعية'], '56':['Wadding, felt & rope','الحشو واللباد والحبال'], '57':['Carpets','السجاد'],
  '58':['Special fabrics','أقمشة خاصة'], '59':['Coated fabrics','أقمشة مغلّفة'], '60':['Knitted fabrics','أقمشة محبوكة'],
  '61':['Knitted clothing','الملابس المحبوكة'], '62':['Woven clothing','الملابس غير المحبوكة'], '63':['Other textile articles','مصنوعات نسيجية أخرى'],
  '64':['Footwear','الأحذية'], '65':['Headgear','أغطية الرأس'], '66':['Umbrellas','المظلات'],
  '67':['Feathers & artificial flowers','الريش والزهور الاصطناعية'], '68':['Stone & cement articles','مصنوعات الحجر والإسمنت'], '69':['Ceramics','الخزف'],
  '70':['Glass','الزجاج'], '71':['Gold, gems & jewellery','الذهب والأحجار الكريمة والمجوهرات'], '72':['Iron & steel','الحديد والصلب'],
  '73':['Iron & steel products','مصنوعات الحديد والصلب'], '74':['Copper','النحاس'], '75':['Nickel','النيكل'],
  '76':['Aluminium','الألومنيوم'], '77':['Reserved','محجوز'], '78':['Lead','الرصاص'],
  '79':['Zinc','الزنك'], '80':['Tin','القصدير'], '81':['Other base metals','معادن أساسية أخرى'],
  '82':['Tools & cutlery','الأدوات وأدوات المائدة'], '83':['Other metal products','مصنوعات معدنية أخرى'], '84':['Machinery','الآلات'],
  '85':['Electrical & electronic equipment','المعدات الكهربائية والإلكترونية'], '86':['Railway equipment','معدات السكك الحديدية'], '87':['Vehicles & parts','المركبات وقطعها'],
  '88':['Aircraft','الطائرات'], '89':['Ships & boats','السفن والقوارب'], '90':['Optical & medical instruments','الأجهزة البصرية والطبية'],
  '91':['Clocks & watches','الساعات'], '92':['Musical instruments','الآلات الموسيقية'], '93':['Arms & ammunition','الأسلحة والذخائر'],
  '94':['Furniture & lighting','الأثاث والإنارة'], '95':['Toys & sports goods','الألعاب والأدوات الرياضية'], '96':['Miscellaneous manufactures','مصنوعات متنوعة'],
  '97':['Art & antiques','التحف والأعمال الفنية'], '99':['Other / unclassified','أخرى / غير مصنّفة'],
};
if (typeof window !== 'undefined') window.HS2 = HS2;
if (typeof module !== 'undefined' && module.exports) module.exports = { HS2 };
