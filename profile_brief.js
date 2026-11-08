    // ===== 启信慧眼单位画像（编制参阅材料时经后端 /api/profile 调取（静态版经跨域代理） · 2026-11-07）=====
    // 数据由 WorkBuddy 会话侧调用启信慧眼已授权接口核验后结构化落盘，构建/部署时随服务端提供；
    // 页面点击「编制并查看参阅材料」后向后端 /api/profile 发起请求调取，前端零凭据、不直连商业数据域名。
    // 命中则展示已核验机构画像并逐字段标注状态；未命中或通道不可用一律如实标注，不伪造、不推断。
    function profileHit(q){ return !!(q && q.profile && q.profile.found && q.profile.profile); }
    function profileReasonText(q){
      var r=q && q.profileReason;
      if(r==="not-in-profile-library") return "该单位未收录于启信慧眼核验画像库";
      if(r==="profile-error" || r==="offline") return "画像通道不可用（离线或后端未启用）";
      if(r==="provider-auth-failed") return "实时画像通道鉴权未通过";
      if(r==="provider-unavailable" || r==="provider-not-configured") return "实时画像通道尚未配置有效密钥";
      if(r==="empty-name") return "缺少机构名称";
      return r ? ("调取未成功：" + r) : "本次未取得画像数据";
    }
    function profileHtml(q){
      var L=[];
      L.push('<h3 class="sub">（九）启信慧眼单位画像（编制时调取 · 可复核）</h3>');
      if(!profileHit(q)){
        L.push('<p class="indent">本次编制已就「'+E((q&&q.name)||"该机构")+'」向后端 <code>/api/profile</code> 发起画像调取，结果为：<b>未取得该单位画像</b>。原因：'+E(profileReasonText(q))+'。</p>');
        L.push('<p class="indent">第三章其余内容仍按既有口径出具：已收录资料库的机构以技能全网检索核验事实为主体，未收录机构为同类机构通用研判，均不因画像调取失败而改变性质或冒充核验结果。</p>');
        L.push('<p><b>补齐路径：</b>在 WorkBuddy 会话中发起「画像补齐 &lt;机构全称&gt;」，由会话侧启信慧眼通道按统一社会信用代码锁定主体、逐字段核验后写入画像库，重新部署后页面刷新即可调取。</p>');
        return L.join("");
      }
      var r=q.profile, p=r.profile, labels=p.fieldLabels||{}, keys=Object.keys(labels), flds=p.fields||{};
      L.push('<p class="indent">数据来源：<b>启信慧眼</b>（'+E(r.provider||"—")+'）｜核验时点 '+E(r.verifiedAt||"—")+'｜坐标系 '+E(r.coordSystem||"—")+'。下表为机构层面公开登记信息，逐字段标注核验状态；'+E((p.policy||{}).scope||"按最小必要原则仅呈现机构层面信息")+'。</p>');
      L.push('<table class="kv-table"><thead><tr><th style="width:28%">画像字段</th><th>启信慧眼载明内容</th><th style="width:12%">状态</th></tr></thead><tbody>');
      keys.forEach(function(k){
        var f=flds[k]||{}, ok=(f.s==="verified" && f.v);
        var cell=ok ? f.v : ((f.note && f.note!=="启信慧眼未载明或未公示") ? ("未检索到公开可核验信息（"+f.note+"）") : "未检索到公开可核验信息");
        L.push('<tr><td>'+E(labels[k])+'</td><td>'+E(cell)+'</td><td>'+(ok?"已核验":"未公示")+'</td></tr>');
      });
      L.push('</tbody></table>');
      if((p.tags||[]).length){
        L.push('<p><b>机构属性标签：</b>'+E(p.tags.join(" / "))+'。<span class="sd">按行内参考口径，仅采用机构属性类标签，风险与涉诉类信息不纳入公开页。</span></p>');
      }
      if(p.geo){
        L.push('<p><b>启信慧眼登记坐标：</b>'+E(String(p.geo.lat))+', '+E(String(p.geo.lng))+'（GCJ-02）。该坐标仅作画像参考，最近网点测算以查询阶段所用定位基准为准，两者口径不一致时以后者为准并列列示，不合并推定。</p>');
      }
      var srcs=p.sources||[];
      if(srcs.length){
        L.push('<p><b>核验接口留痕：</b></p><ol class="tight">');
        srcs.forEach(function(s){ L.push('<li>'+E(s.label||"")+'（<code>'+E(s.api_ref||"")+'</code>）</li>'); });
        L.push('</ol>');
      }
      L.push('<p><b>使用要求：</b>本画像为编制时调取的公开登记信息，具有时点性；开户主体资格、预算管理口径、账户用途与负责人信息须按第九章清单经官方渠道核实后现场补录。画像不构成客户身份识别结论、授信意向或服务承诺。</p>');
      return L.join("");
    }
    function profileText(q){
      var A=["【启信慧眼单位画像（编制时调取 · 可复核）】"];
      if(!profileHit(q)){
        A.push("  本次编制已向后端 /api/profile 发起调取，未取得「"+((q&&q.name)||"该机构")+"」画像。原因："+profileReasonText(q)+"。");
        A.push("  第三章其余内容按既有口径出具，不因画像调取失败而冒充核验结果。");
        A.push("  补齐路径：在 WorkBuddy 会话中发起「画像补齐 <机构全称>」，核验落盘并重新部署后刷新生效。");
        return A;
      }
      var r=q.profile, p=r.profile, labels=p.fieldLabels||{}, flds=p.fields||{};
      A.push("  数据来源：启信慧眼（"+(r.provider||"—")+"）｜核验时点 "+(r.verifiedAt||"—")+"｜坐标系 "+(r.coordSystem||"—"));
      A.push("  口径："+((p.policy||{}).scope||"按最小必要原则仅呈现机构层面信息"));
      Object.keys(labels).forEach(function(k){
        var f=flds[k]||{}, ok=(f.s==="verified" && f.v);
        A.push("  " + labels[k] + "：" + (ok ? f.v : "未检索到公开可核验信息") + "【" + (ok?"已核验":"未公示") + "】");
      });
      if((p.tags||[]).length) A.push("  机构属性标签：" + p.tags.join(" / "));
      if(p.geo) A.push("  启信慧眼登记坐标：" + p.geo.lat + ", " + p.geo.lng + "（GCJ-02，仅作画像参考）");
      (p.sources||[]).forEach(function(s,i){ A.push("  接口留痕 "+(i+1)+"："+(s.label||"")+"（"+(s.api_ref||"")+"）"); });
      A.push("  使用时须按第九章清单经官方渠道复核；画像不构成客户身份识别结论、授信意向或服务承诺。");
      return A;
    }
