    // ===== 技能全网检索核验资料库（前端零 Key · 2026-11-07）=====
    // 数据由 WorkBuddy 会话侧技能全网检索公开渠道、逐字段交叉核验后结构化落盘，
    // 构建时由 intel_pipeline.py 校验并内联为 window.ORG_INTEL；页面不发起任何外部请求。
    // 命中资料库时，第三章以「已核验事实 + 证据索引」替代同类机构通用研判；
    // 未命中时如实回退为「职务口径 + 通行架构 + 现场补录」，不得伪装已核验。
    var INTEL_DATA = window.ORG_INTEL || {orgs:[]};
    var INTEL_ORGS = INTEL_DATA.orgs || [];
    var INTEL_STATUS = {
      verified:"官方页面直接载明", cross:"多来源交叉一致",
      partial:"官方原文摘录（完整条款见来源）", conflict:"来源口径存在差异（并列列示）",
      unverified:"未检索到公开可核验信息"
    };
    function intelStatus(s){ return INTEL_STATUS[s] || "状态未标注"; }
    function intelNorm(s){ return String(s==null?"":s).replace(/[\s（）()·、,，。.\-—]/g,"").toLowerCase(); }

    // 机构名匹配：全称 / 别名精确优先，其次做包含式模糊匹配（要求 >=4 字且有足够重合度）
    function lookupIntel(name){
      var t=intelNorm(name);
      if(t.length<4) return null;
      var best=null, bestScore=0;
      for(var i=0;i<INTEL_ORGS.length;i++){
        var o=INTEL_ORGS[i], names=[o.name].concat(o.aliases||[]);
        for(var j=0;j<names.length;j++){
          var n=intelNorm(names[j]); if(!n) continue;
          if(n===t) return o;
          var sc=0;
          if(n.indexOf(t)===0 || t.indexOf(n)===0) sc=Math.min(n.length,t.length)*2;
          else if(n.indexOf(t)!==-1 || t.indexOf(n)!==-1) sc=Math.min(n.length,t.length);
          if(sc>bestScore){ bestScore=sc; best=o; }
        }
      }
      return bestScore>=4 ? best : null;
    }
    function intelField(o,k){ return (o && o.fields && o.fields[k]) || null; }
    function intelFieldText(f){
      if(!f) return "未检索到公开可核验信息";
      if(f.s==="unverified") return f.note || "未检索到公开可核验信息";
      var v=f.v;
      if(Array.isArray(v)) return v.map(function(r){ return Array.isArray(r)?r.join(" "):String(r); }).join("；");
      return String(v==null?"":v);
    }
    function intelCoverage(o){
      var f=(o&&o.fields)||{}, n=0, ok=0, un=0;
      Object.keys(f).forEach(function(k){ n++; if(f[k].s==="unverified") un++; else ok++; });
      return {fields:n, ok:ok, unverified:un, sources:Object.keys((o&&o.sources)||{}).length,
              conflicts:(o&&o.conflicts||[]).length};
    }
    // 将字段统一转成 [项目, 内容, 核验状态] 三列，供 renderTable 渲染
    function intelFactRows(f, label){
      if(!f) return [[label||"项目","未检索到公开可核验信息",intelStatus("unverified")]];
      if(f.s==="unverified") return [[label||"项目", f.note||"未检索到公开可核验信息", intelStatus(f.s)]];
      var v=f.v, out=[];
      if(Array.isArray(v)){
        v.forEach(function(r){
          var a=Array.isArray(r)?r.slice():[String(r)];
          var item=a[0]||"";
          var desc=a.slice(1).filter(function(x){return x!=null&&x!=="";}).join("｜");
          out.push([item, desc, intelStatus(f.s)]);
        });
      } else {
        out.push([label||"项目", String(v==null?"":v) + (f.note?"（"+f.note+"）":""), intelStatus(f.s)]);
      }
      return out;
    }
    function intelSourceList(o, keys){
      var src=(o&&o.sources)||{}, out=[];
      (keys||[]).forEach(function(k){ if(src[k]) out.push(src[k]); });
      return out;
    }
    // 证据索引（HTML）：链接由页面拼装，点击后由浏览器打开官方来源，页面不抓取、不代理
    function intelEvidenceHtml(o){
      if(!o) return "";
      var src=o.sources||{}, L=[];
      L.push('<h3 class="sub">（八）全网检索证据索引与口径差异（技能补齐 · 可复核）</h3>');
      L.push('<p class="indent">下列来源由会话侧技能在执行全网检索时逐项核验并留痕，核验日期 '+E(o.verifiedAt||"—")+
        '。点击链接可在浏览器中复核原文；页面本身不抓取、不缓存、不代理任何外部查询，亦不依赖任何数据接口授权。</p>');
      L.push('<div class="verify-links">');
      Object.keys(src).forEach(function(k,i){
        var s=src[k];
        L.push('<a href="'+E(s.u)+'" target="_blank" rel="noopener noreferrer">'+
          '<span class="vl__n">'+String(i+1)+'</span>'+
          '<span class="vl__t">'+E(s.t)+'<span class="sd">'+E(s.k)+' · '+E(s.d)+'</span></span>'+
          '<span class="vl__go">↗</span></a>');
      });
      L.push('</div>');
      if((o.conflicts||[]).length){
        L.push('<p><b>口径差异与时点说明（并列列示，不合并推定）：</b></p><ol class="tight">');
        o.conflicts.forEach(function(c){ L.push('<li>'+E(c)+'</li>'); });
        L.push('</ol>');
      }
      L.push('<p><b>待核实事项：</b>标注「未检索到公开可核验信息」的字段，以及下属单位法人资格、单独核算与开户主体等，须按第九章清单经官方渠道核实后现场补录。</p>');
      return L.join("");
    }
    function intelEvidenceText(o){
      if(!o) return [];
      var src=o.sources||{}, A=["【全网检索证据索引与口径差异（技能补齐 · 可复核）】",
        "核验日期："+(o.verifiedAt||"—")+"；下列来源由会话侧技能全网检索时逐项留痕，页面不抓取、不代理、不依赖接口授权。"];
      Object.keys(src).forEach(function(k,i){ var s=src[k]; A.push("  "+(i+1)+". "+s.t+"｜"+s.k+"｜"+s.d+"｜"+s.u); });
      (o.conflicts||[]).forEach(function(c,i){ A.push("  口径差异 "+(i+1)+"："+c); });
      A.push("  标注「未检索到公开可核验信息」的字段须按第九章清单经官方渠道核实后现场补录。");
      return A;
    }

    // 命中资料库时的第三章：以已核验事实为主体，逐小节给出真实信息与证据状态
    function intelProfileSection(q,p){
      var o=q.intel, f=(o&&o.fields)||{}, n=q.name||"机构";
      var cov=intelCoverage(o), B=[];
      var HEAD=["项目","全网检索已核验内容","核验状态"];

      B.push({sub:"（一）资料库命中情况与信息分级",
        intro:"本机构已由 WorkBuddy 会话侧技能执行全网检索并结构化补齐。页面仅调取已核验事实，不发起任何外部接口请求，无需任何 API 授权。",
        table:{head:["项目","内容"],kv:true,rows:[
          ["资料库规范名称",o.name],
          ["核验日期",o.verifiedAt||"—"],
          ["已补齐字段",cov.ok+" 项（另有 "+cov.unverified+" 项如实标注未检索到）"],
          ["证据来源",cov.sources+" 条（详见本章第八节索引）"],
          ["口径差异说明",cov.conflicts+" 条"],
          ["机构类别（研判）",p?p.label:"—"],
          ["公开坐标",String(o.geo.lat)+", "+String(o.geo.lng)+"（"+intelStatus(o.geo.s)+"）"]
        ]},
        paras:["<b>分级口径：</b>公开页面仅列机构层面事实；官网公开的领导姓名与办公联系方式存于会话侧内部资料库，按最小必要原则不在本页面展示，正式材料应在 WorkBuddy 会话侧按行内规范生成。",
               "<b>使用要求：</b>「未检索到公开可核验信息」不等于不存在，须按第九章清单经官方渠道核实；已核验内容的时效以各来源发布日期为准。"]});

      B.push({sub:"（二）主要及相关负责人（核验状态 · 职务口径 · 现场补录）",
        intro:"领导信息时效性强，本页按分级口径列示技能核验状态与职务口径，不预置自然人姓名；现场补录可即时回填本章。",
        table:{head:["序号","职务口径","姓名 / 名称","走访对接关注点","信息状态"],
          rows:(typeof LEADER_ROLES!=="undefined"?LEADER_ROLES:[]).map(function(r,i){
            return [String(i+1),r.role,r.key?(typeof F!=="undefined"?F(r.key):"—"):"—",r.focus,
                    r.key?(typeof FS!=="undefined"?FS(r.key):"不涉及"):"不涉及"];
          })},
        paras:["<b>技能核验状态：</b>"+E(intelFieldText(intelField(o,"leadersStatus"))||"未检索到公开可核验信息"),
               "<b>核实依据：</b>单位官网「领导信息 / 领导之窗」栏目、政府信息公开平台、最新任免文件与官方公开报道；不得依据转载、汇编或非公开渠道填写。",
               "<b>对接顺序：</b>先由总行公司金融部按正式渠道预约，经办公室（综合处）归口后，再与财务部门对接具体事项。"]});

      B.push({sub:"（三）主要职能（官方公布条款 · 已核验）",
        intro:"下表为公开渠道载明的机构主要职责，采用原文摘录；标注「原文摘录」的，完整条款见本章第八节对应来源。",
        table:{head:HEAD,rows:intelFactRows(f.functions,"主要职责")},
        paras:["<b>口径提示：</b>"+E((f.functions&&f.functions.note)||""),
               "<b>研判边界：</b>第四章业务场景与第六章合作方向仍为同类机构通用研判，不代表本机构已提出相应金融服务需求。"]});

      B.push({sub:"（四）内设机构及职责分工（官方公布清单 · 已核验）",
        intro:"下表列示官方公开的内设机构名称与职责口径，用于判断应接洽的归口部门；合并列示的处室以官网原清单为准。",
        table:{head:HEAD,rows:intelFactRows(f.innerOrgs,"内设机构")},
        paras:["<b>口径提示：</b>"+E((f.innerOrgs&&f.innerOrgs.note)||""),
               "<b>已核实内设机构（现场补录）：</b>"+E(typeof F!=="undefined"?F("innerOrg"):"待核实"),
               "<b>核实要点：</b>财务（计划财务）部门通常为账户、结算与对账主归口；办公室（综合处）为函件与会务归口；涉及收费、采购、人员经费的事项须分别确认对应处室及审批链条。"]});

      B.push({sub:"（五）上级主管与业务指导单位（官方载明 · 已核验）",
        intro:"下表按官方公开文件载明的领导关系、归口关系与共建 / 举办关系列示；未取得官方明确表述的关系一律标注未核验，不作推定。",
        table:{head:HEAD,rows:intelFactRows(f.superiors,"关系层级")},
        paras:["<b>口径提示：</b>"+E((f.superiors&&f.superiors.note)||""),
               "<b>上级主管单位（现场补录）：</b>"+E(typeof F!=="undefined"?F("superior"):"待核实"),
               "<b>关键影响：</b>预算单位属性、开户审批链条、资金存放决策程序与竞争性选择安排，通常由上级主管部门及同级综合管理部门规定确定。"]});

      B.push({sub:"（六）下属及归口管理单位（官方载明 · 已核验）",
        intro:"下表列示官方公开的下属 / 直属 / 归口管理单位清单；是否具备独立法人资格、是否单独核算与分别开户，均须另行核实。",
        table:{head:HEAD,rows:intelFactRows(f.subordinates,"下属单位")},
        paras:["<b>口径提示：</b>"+E((f.subordinates&&f.subordinates.note)||""),
               "<b>下属 / 归口管理单位（现场补录）：</b>"+E(typeof F!=="undefined"?F("subordinate"):"待核实"),
               "<b>核实要点：</b>下属单位是否具备独立法人资格、是否单独核算、是否已分别开立账户，直接决定可否开展资金归集与统一对账，不得先行推定。"]});

      return {
        t:"三、单位治理与组织画像（负责人 / 内设架构与职能 / 上级及下属单位）",
        intro:"本章主体由技能全网检索的已核验事实构成：明确机构主要职能、内设架构与职责分工、上级及下属管理单位，并逐项标注核验状态、来源与口径差异；负责人按信息分级口径列示核验状态与职务口径。",
        flag:"已核验事实均附证据索引与核验日期；未检索到的字段如实标注，不以同类机构通行架构填充；负责人姓名按最小必要原则不在公开页面列示。",
        blocks:B
      };
    }

    // 未命中资料库时的如实提示（追加到通用研判版第三章）
    function intelMissingHtml(q){
      return '<h3 class="sub">（八）资料库收录状态与补齐路径</h3>'+
        '<p class="indent">本机构尚未纳入技能全网检索核验资料库，本章（一）至（六）为同类机构通用研判，非本机构事实。页面不联网、不代理查询，也不会以模板内容冒充核验结果。</p>'+
        '<p><b>补齐方式：</b>在 WorkBuddy 会话中指定机构名称发起「全网检索补齐」，由技能按检索式矩阵核对官方公开来源、逐字段留痕后写入资料库，重新构建并部署，页面刷新后即自动命中已核验事实。</p>'+
        '<p><b>当前可用：</b>第三章（七）官方核验直达入口、现场补录与第九章核实清单；页面不携带地图密钥、不直连地图域名，实时定位经同源后端代理完成，编制阶段不发起外部网络请求。</p>';
    }
    function intelMissingText(){
      return ["【资料库收录状态与补齐路径】",
        "本机构尚未纳入技能全网检索核验资料库，本章（一）至（六）为同类机构通用研判，非本机构事实；页面不联网、不代理查询，不以模板内容冒充核验结果。",
        "补齐方式：在 WorkBuddy 会话中指定机构名称发起「全网检索补齐」，由技能核对官方公开来源、逐字段留痕后写入资料库，重新构建部署后页面即自动命中。",
        "当前可用：第三章（七）官方核验直达入口、现场补录与第九章核实清单；页面不携带地图密钥、不直连地图域名，实时定位经同源后端代理完成，编制阶段不发起外部网络请求。"];
    }
