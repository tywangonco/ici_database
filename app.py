import streamlit as st
import re

# 設定頁面資訊與版面大小
st.set_page_config(
    page_title="ICI 給付條件查詢系統",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="expanded"
)

# 依最新健保給付規定更新的 ici_database 字典
ici_database = {
    "非小細胞肺癌 (NSCLC)": {
        "鞏固治療": {
            "藥物": ["durvalumab"],
            "單用/併用": "單獨使用",
            "PD_L1_條件": "PD-L1 >= 1% (Ventana SP263)",
            "臨床條件": "第三期局部晚期、無法手術切除。非鱗狀癌者需為EGFR/ALK/ROS-1腫瘤基因原生型、鱗狀癌者需為EGFR/ALK腫瘤基因原生型。病人須於接受根治性同步放射治療合併至少2個週期含鉑化療後無惡化(無PD)，且至多使用12個月。"
        },
        "第一線用藥 (單用)": {
            "藥物": ["pembrolizumab", "atezolizumab", "cemiplimab"],
            "單用/併用": "單獨使用",
            "PD_L1_條件": "pembrolizumab: TPS >= 50% (Dako 22C3/Ventana SP263); atezolizumab: TC >= 50% 或 IC >= 10% (Ventana SP142); cemiplimab: TPS >= 50% (Dako 22C3或Ventana SP263*)[cite: 2]",
            "臨床條件": "轉移性非小細胞肺癌成人病人。非鱗狀癌者需為EGFR/ALK/ROS-1腫瘤基因原生型、鱗狀癌者需為EGFR/ALK腫瘤基因原生型。"
        },
        "第一線用藥 (非鱗狀, 併用)": {
            "藥物": ["pembrolizumab", "atezolizumab"],
            "單用/併用": "必須併用 (pembro + pemetrexed + 鉑類; atezo + bevacizumab + carbo/paclitaxel)",
            "PD_L1_條件": "不需檢附報告",
            "臨床條件": "轉移性且不具有EGFR/ALK/ROS-1腫瘤基因異常的非鱗狀非小細胞肺癌。"
        },
        "第一線用藥 (鱗狀, 併用)": {
            "藥物": ["pembrolizumab"],
            "單用/併用": "必須併用 (與 carboplatin 及 paclitaxel 併用至多使用4個療程，接續單用)",
            "PD_L1_條件": "TPS 1~49%",
            "臨床條件": "轉移性鱗狀非小細胞肺癌。"
        },
        "第二線用藥 (鱗狀)": {
            "藥物": ["pembrolizumab", "nivolumab", "atezolizumab"],
            "單用/併用": "單獨使用",
            "PD_L1_條件": "pembrolizumab: TPS >= 50%; nivolumab: TC >= 50%; atezolizumab: TC >= 50% 或 IC >= 10%",
            "臨床條件": "先前已使用過platinum類化學治療失敗後，又有疾病惡化，且EGFR/ALK腫瘤基因為原生型之晚期鱗狀非小細胞肺癌。"
        },
        "第三線用藥 (肺腺癌)": {
            "藥物": ["pembrolizumab", "nivolumab", "atezolizumab"],
            "單用/併用": "單獨使用",
            "PD_L1_條件": "pembrolizumab: TPS >= 50%; nivolumab: TC >= 50%; atezolizumab: TC >= 50% 或 IC >= 10%",
            "臨床條件": "先前已使用過platinum類及docetaxel/paclitaxel類二線(含)以上化學治療均失敗，又有疾病惡化，且EGFR/ALK/ROS-1腫瘤基因為原生型之晚期非小細胞肺腺癌。"
        }
    },
    "晚期肝細胞癌 (HCC)": {
        "第一線用藥": {
            "藥物": ["atezolizumab + bevacizumab", "durvalumab + tremelimumab"],
            "單用/併用": "必須併用",
            "PD_L1_條件": "不需檢附報告",
            "臨床條件": "Child-Pugh A class晚期肝細胞癌成人患者。未曾接受全身性療法。需具備肝外轉移、大血管侵犯，或經 T.A.C.E. 於12個月內 >= 3 次局部治療失敗紀錄。排除曾接受器官移植、正在接受免疫抑制藥物治療、有上消化道出血之疑慮且未接受完全治療者。與 sorafenib、lenvatinib 僅得擇一給付，不得互換。atezolizumab與bevacizumab併用或durvalumab與tremelimumab併用治療失敗後，不得申請使用regorafenib或ramucirumab[cite: 2]。"
        },
        "後線治療 (舊案續用)": {
            "藥物": ["nivolumab"],
            "單用/併用": "單獨使用",
            "PD_L1_條件": "不需檢附報告",
            "臨床條件": "Child-Pugh A class肝細胞癌。先前經T.A.C.E.於12個月內>=3次局部治療失敗。已使用過至少一線標靶藥物治療失敗且惡化。未曾進行肝臟移植。限於109年4月1日前經審核同意用藥符合續用申請條件者。"
        }
    },
    "胃癌": {
        "第一線用藥": {
            "藥物": ["nivolumab"],
            "單用/併用": "必須併用 (與 fluoropyrimidine 及 oxaliplatin 併用)",
            "PD_L1_條件": "CPS >= 5",
            "臨床條件": "第一線治療晚期或轉移性且不具有HER2過度表現的胃癌病人（不含胃腸基質瘤及神經內分泌腫瘤/癌）。與 zolbetuximab 僅得擇一使用，且治療失敗時不可互換。"
        },
        "後線治療 (舊案續用)": {
            "藥物": ["nivolumab"],
            "單用/併用": "單獨使用",
            "PD_L1_條件": "CPS >= 1",
            "臨床條件": "先前已使用過二線(含)以上化學治療均失敗，又有疾病惡化的轉移性胃腺癌。且於109年4月1日前經審核同意用藥，後續評估符合續用者。"
        }
    },
    "大腸直腸癌": {
        "第一線用藥": {
            "藥物": ["pembrolizumab"],
            "單用/併用": "單獨使用",
            "PD_L1_條件": "不需檢附報告",
            "臨床條件": "做為無法切除或轉移性高微衛星不穩定性(MSI-H)或錯誤配對修復功能不足性(dMMR)大腸直腸癌(CRC)之成年病人第一線治療。"
        }
    },
    "食道鱗狀細胞癌": {
        "第一線用藥": {
            "藥物": ["nivolumab"],
            "單用/併用": "必須併用 (與 fluoropyrimidine 及 cisplatin 或 oxaliplatin 併用)",
            "PD_L1_條件": "TC >= 1%",
            "臨床條件": "用於無法接受化學放射性治療或手術切除等治癒性治療之晚期或轉移性食道鱗狀細胞癌成人病人的第一線治療。"
        },
        "第二線用藥": {
            "藥物": ["nivolumab"],
            "單用/併用": "單獨使用",
            "PD_L1_條件": "TC >= 1%",
            "臨床條件": "曾接受合併含鉑及fluoropyrimidine化學治療之後惡化的無法切除晚期或復發性食道鱗狀細胞癌病人。"
        }
    },
    "膽道癌": {
        "第一線用藥": {
            "藥物": ["durvalumab"],
            "單用/併用": "必須併用 (與 cisplatin 及 gemcitabine 併用至多使用8個療程，接續單用)",
            "PD_L1_條件": "不需檢附報告",
            "臨床條件": "先前未接受過治療或不可手術之局部晚期或轉移性膽道癌。須排除壺腹癌、曾接受異體器官移植、具有或曾有活動性自體免疫或發炎性疾病。"
        }
    },
    "泌尿道上皮癌": {
        "第一線用藥 (單用)": {
            "藥物": ["pembrolizumab", "atezolizumab"],
            "單用/併用": "單獨使用",
            "PD_L1_條件": "pembrolizumab: CPS >= 10; atezolizumab: IC >= 5% (註: atezo限於113年8月1日前審核同意)",
            "臨床條件": "不適合接受化學治療之轉移性泌尿道上皮癌。需符合聽力受損 (CTCAE grade≧2)、周邊神經病變 (CTCAE grade≧2) 或 CIRS score > 6 條件之一。單獨使用 pembrolizumab 須符合 eGFR>30 且 <60 mL/min/1.73m2[cite: 2]。"
        },
        "第一線用藥 (併用)": {
            "藥物": ["nivolumab"],
            "單用/併用": "必須併用 (與 cisplatin 及 gemcitabine 併用至多6個療程，接續單用)",
            "PD_L1_條件": "TC >= 1%",
            "臨床條件": "無法切除或轉移性泌尿道上皮癌。nivolumab 併用化療須符合 eGFR >= 60 mL/min/1.73m2[cite: 2]。"
        },
        "第二線用藥": {
            "藥物": ["pembrolizumab", "nivolumab", "atezolizumab"],
            "單用/併用": "單獨使用",
            "PD_L1_條件": "pembrolizumab: CPS >= 10; nivolumab: TC >= 5%; atezolizumab: IC >= 5% (註: atezo限於113/8/1前審核同意)",
            "臨床條件": "先前已使用過platinum類化學治療失敗後疾病惡化的局部晚期無法切除或轉移性患者。eGFR>30 mL/min/1.73m2。"
        },
        "維持療法": {
            "藥物": ["avelumab"],
            "單用/併用": "單獨使用",
            "PD_L1_條件": "不需檢附報告",
            "臨床條件": "接受第一線含鉑化學治療4至6個療程後，疾病未惡化且達部分緩解 (PR) 或呈穩定狀態 (SD) 之無法手術切除局部晚期或轉移性患者。eGFR>30 mL/min/1.73m2。"
        }
    },
    "頭頸部鱗狀細胞癌 (不含鼻咽癌)": {
        "第一線用藥": {
            "藥物": ["pembrolizumab"],
            "單用/併用": "單獨使用",
            "PD_L1_條件": "CPS >= 20",
            "臨床條件": "先前未曾接受全身性治療且無法手術切除之復發性或轉移性(第三期或第四期)。"
        },
        "第二線用藥": {
            "藥物": ["pembrolizumab", "nivolumab"],
            "單用/併用": "單獨使用",
            "PD_L1_條件": "pembrolizumab: TPS >= 50%; nivolumab: TC >= 10%",
            "臨床條件": "先前已使用過platinum類化學治療失敗後，又有疾病惡化的復發性或轉移性(第三期或第四期)。"
        }
    },
    "黑色素瘤": {
        "晚期/轉移性": {
            "藥物": ["pembrolizumab", "nivolumab"],
            "單用/併用": "單獨使用",
            "PD_L1_條件": "不需檢附報告",
            "臨床條件": "腫瘤無法切除或轉移之第三期或第四期，先前曾接受過至少一次全身性治療失敗者。需另檢附BRAF腫瘤基因檢測結果。"
        }
    },
    "早期三陰性乳癌": {
        "術前前導至術後輔助": {
            "藥物": ["pembrolizumab"],
            "單用/併用": "併用接單用 (前導：與 carboplatin 和 paclitaxel 併用至多4個療程 -> 加上 cyclophosphamide 和 doxorubicin 或 epirubicin 併用至多4個療程；輔助：單用至多9個療程)",
            "PD_L1_條件": "不需檢附報告",
            "臨床條件": "非轉移性、第II期至第IIIb期成年病人。初次申請時需檢附ER、PR及HER2為陰性之檢測報告。術後輔助治療須為接受過術前前導性治療後，限手術後未達pCR者，且須檢附發現有殘餘的侵襲性癌症(non-pCR)佐證。用於術後輔助治療，pembrolizumab與olaparib僅能擇一支付[cite: 2]。"
        }
    },
    "小細胞肺癌": {
        "擴散期": {
            "藥物": ["atezolizumab", "durvalumab"],
            "單用/併用": "必須併用 (atezo + carboplatin + etoposide; 或 durva + etoposide + carboplatin 或 cisplatin)",
            "PD_L1_條件": "不需檢附報告",
            "臨床條件": "適用於先前未曾接受化療，且無腦部或無脊髓轉移之擴散期(extensive stage)小細胞肺癌。"
        }
    },
    "惡性肋膜間皮瘤": {
        "第一線用藥": {
            "藥物": ["ipilimumab + nivolumab"],
            "單用/併用": "必須併用",
            "PD_L1_條件": "不需檢附報告",
            "臨床條件": "無法切除之惡性肋膜間皮瘤且病理組織顯示為非上皮型(Non-epithelioid)病人的第一線治療。"
        }
    },
    "典型何杰金氏淋巴瘤": {
        "復發或惡化": {
            "藥物": ["pembrolizumab", "nivolumab"],
            "單用/併用": "單獨使用",
            "PD_L1_條件": "不需檢附報告",
            "臨床條件": "先前已接受自體造血幹細胞移植(HSCT)與移植後brentuximab vedotin (BV)治療，但又復發或惡化。需另檢附自體造血幹細胞移植之病歷紀錄。"
        }
    },
    "晚期腎細胞癌": {
        "後線治療": {
            "藥物": ["nivolumab"],
            "單用/併用": "單獨使用",
            "PD_L1_條件": "不需檢附報告",
            "臨床條件": "先前已使用過至少二線標靶藥物治療均失敗，又有疾病惡化。病理上為亮細胞癌(clear cell renal carcinoma)。"
        }
    },
    "默克細胞癌": {
        "轉移性": {
            "藥物": ["avelumab"],
            "單用/併用": "單獨使用",
            "PD_L1_條件": "不需檢附報告",
            "臨床條件": "先前已使用過platinum類化學治療失敗後，又有疾病惡化之轉移性第四期默克細胞癌。"
        }
    }
}

def format_citation(text):
    """使用正規表達式將 [cite: ...] 和 [條文：XXX] 轉換為美化的 Markdown 標籤"""
    if not text:
        return ""
    # 處理 [cite: N] 格式
    text = re.sub(r'\[cite:\s*(\d+(?:,\s*\d+)*)\]', r'**[參考 \1]**', text)
    # 處理 [條文：XXX] 格式
    text = re.sub(r'\[條文：(.*?)\]', r'  *(依據：\1)* ', text)
    return text

def render_bullet_points(text):
    """將含有句號的字串分割為條列式呈現"""
    if not text:
        return ""
    # 用句號分割，過濾掉空白的，最後再加上句號補回
    points = [p.strip() + "。" for p in text.split("。") if p.strip()]
    bullet_list = ""
    for point in points:
        bullet_list += f"- {point}\n"
    return bullet_list

def main():
    st.title("🛡️ 健保免疫檢查點抑制劑 (ICI)")
    st.subheader("給付條件查詢系統")
    st.markdown("本系統提供快速查詢各類癌症健保給付之免疫檢查點抑制劑相關條件，節省人工查找規範之時間。")
    st.markdown("---")

    # [重要排除條件與提醒] 使用 warning 高亮
    st.warning(
        "**⚠️ 全域給付重要提醒 & 排除條件**\n"
        "1. **給付時程期限**：自初次處方用藥日起算 **2 年**。\n"
        "2. **互換與合併限制**：各適應症限給付一種 ICI 藥物，且**不得互換**或於治療期間合併使用他種 ICI 藥物（除特定明確規範之雙免疫組合如 ipilimumab + nivolumab）。\n"
        "3. **其他一般排除條件**：若有自體免疫疾病、需使用全身性免疫抑制劑、或為曾接受器官移植之患者，通常不予給付或需進行專案特別審查。"
    )

    # 第一層：選擇癌別
    st.markdown("### 第一步：請選擇癌別")
    cancer_types = list(ici_database.keys())
    selected_cancer = st.selectbox(
        "癌別 (Cancer Type)", 
        options=["請選擇癌別..."] + cancer_types,
        index=0
    )

    if selected_cancer and selected_cancer != "請選擇癌別...":
        scenarios = list(ici_database[selected_cancer].keys())
        
        st.markdown("### 第二步：請選擇治療線別/情境")
        
        # 若該癌別只有單一情境，則自動選定
        if len(scenarios) == 1:
            selected_scenario = scenarios[0]
            st.info(f"💡 **系統已為您自動選擇**：`{selected_scenario}` （因該癌別目前僅有此單一給付情境）")
        else:
            selected_scenario = st.selectbox(
                "治療線別 / 情境 (Treatment Line / Scenario)", 
                options=["請選擇情境..."] + scenarios,
                index=0
            )

        if selected_scenario and selected_scenario != "請選擇情境...":
            # 取得結果對應資料
            data = ici_database[selected_cancer][selected_scenario]
            drugs = "、".join(data.get("藥物", []))
            mode = data.get("單用/併用", "")
            pd_l1 = data.get("PD_L1_條件", "")
            clinical = data.get("臨床條件", "")

            # 套用標籤格式化
            pd_l1 = format_citation(pd_l1)
            clinical = format_citation(clinical)
            mode = format_citation(mode)

            st.markdown("---")
            st.markdown("### 第三步：查詢結果與條件")

            # 在 Success 的區塊中呈現詳細內容
            with st.container():
                st.success("✅ **符合條件之藥物與相關給付規定**")
                
                # 藥物與處方模式
                st.markdown(f"### 💊 適用藥物： `{drugs}`")
                st.markdown(f"**⚙️ 給付模式**： {mode}")
                
                st.markdown("---")
                
                # 臨床條件限制
                st.markdown("**🏥 臨床條件限制**：")
                st.markdown(render_bullet_points(clinical))
                
                # 判斷是否含有排除相關字眼，如有則額外用 warning 標註
                if "排除" in clinical:
                    st.warning("⚠️ **注意此情境有特定排除條件，請留意上述臨床條件之說明。**")
                
                # 生物標記 (PD-L1) 規定
                st.markdown("**🔬 生物標記 (PD-L1 / 基因等) 規定**：")
                # 同樣做條列化處理（如果有的話，對於 PD-L1 也適用分段）
                # 有些會使用 ";" 分隔不同藥物
                if ";" in pd_l1:
                    pd_bullets = [p.strip() for p in pd_l1.split(";")]
                    for pb in pd_bullets:
                        st.markdown(f"- {pb}")
                else:
                    st.markdown(render_bullet_points(pd_l1))
                    
    st.markdown("---")
    st.caption("📝 免責聲明：本系統依據使用者提供之資料庫整理，實際給付規定及詳細限制請以中央健康保險署最新公告之「全民健康保險藥物給付項目及支付標準」為準。")

if __name__ == "__main__":
    main()
