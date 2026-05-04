import streamlit as st
import re

# 設定頁面資訊與版面大小
st.set_page_config(
    page_title="ICI 給付條件查詢系統",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="expanded"
)

# 直接內建 ici_database 字典，方便未來抽換或更新資料。
ici_database = {
    "非小細胞肺癌 (NSCLC)": {
        "鞏固治療": {
            "藥物": ["durvalumab"],
            "單用/併用": "單獨使用 [條文：9.69-1]",
            "PD_L1_條件": "PD-L1 >= 1% (Ventana SP263) [條文：9.69-1-(2), 9.69-3-(3)附表]",
            "臨床條件": "第三期局部晚期、無法手術切除。非鱗狀需 EGFR/ALK/ROS-1 原生型，鱗狀需 EGFR/ALK 原生型。需於根治性同步放射治療合併至少2個週期含鉑化療後無惡化，且至多使用 12 個月 [條文：9.69-1-(2)]。"
        },
        "第一線用藥 (單用)": {
            # 新增 cemiplimab 作為第一線用藥[cite: 2]
            "藥物": ["pembrolizumab", "atezolizumab", "cemiplimab"],
            "單用/併用": "單獨使用 [條文：9.69-1]",
            # 更新 cemiplimab 的 PD-L1 條件[cite: 2]
            "PD_L1_條件": "pembrolizumab / cemiplimab: TPS >= 50% (Dako 22C3/Ventana SP263); atezolizumab: TC >= 50% 或 IC >= 10% (Ventana SP142) [條文：9.69-3-(3)附表]",
            "臨床條件": "轉移性成人病人。非鱗狀需 EGFR/ALK/ROS-1 原生型，鱗狀需 EGFR/ALK 原生型 [條文：9.69-1-(2)]。"
        },
        "第一線用藥 (非鱗狀, 併用)": {
            "藥物": ["pembrolizumab", "atezolizumab"],
            "單用/併用": "必須併用 (pembro + pemetrexed + 鉑類; atezo + bevacizumab + carbo/paclitaxel) [條文：9.69-2-(2)]",
            "PD_L1_條件": "不需檢附報告 [條文：9.69-3-(3)附表]",
            "臨床條件": "轉移性且不具有 EGFR/ALK/ROS-1 腫瘤基因異常 [條文：9.69-2-(2)]。"
        },
        "第一線用藥 (鱗狀, 併用)": {
            "藥物": ["pembrolizumab"],
            "單用/併用": "必須併用 (與 carboplatin 及 paclitaxel 併用至多4個療程，接續單用) [條文：9.69-2-(2)]",
            "PD_L1_條件": "TPS 1~49% [條文：9.69-3-(3)附表]",
            "臨床條件": "轉移性鱗狀非小細胞肺癌 [條文：9.69-2-(2)]。"
        },
        "第二線用藥 (鱗狀)": {
            "藥物": ["pembrolizumab", "nivolumab", "atezolizumab"],
            "單用/併用": "單獨使用 [條文：9.69-1]",
            "PD_L1_條件": "pembrolizumab: TPS >= 50%; nivolumab: TC >= 50%; atezolizumab: TC >= 50% 或 IC >= 10% [條文：9.69-3-(3)附表]",
            "臨床條件": "先前已使用過 platinum 類化學治療失敗後疾病惡化，且 EGFR/ALK 為原生型之晚期病人 [條文：9.69-1-(2)]。"
        },
        "第三線用藥 (肺腺癌)": {
            "藥物": ["pembrolizumab", "nivolumab", "atezolizumab"],
            "單用/併用": "單獨使用 [條文：9.69-1]",
            "PD_L1_條件": "pembrolizumab: TPS >= 50%; nivolumab: TC >= 50%; atezolizumab: TC >= 50% 或 IC >= 10% [條文：9.69-3-(3)附表]",
            "臨床條件": "先前已使用過 platinum 類及 docetaxel/paclitaxel 類二線(含)以上化療均失敗，又有疾病惡化，且 EGFR/ALK/ROS-1 原生型之晚期非小細胞肺腺癌 [條文：9.69-1-(2)]。"
        }
    },
    "晚期肝細胞癌 (HCC)": {
        "第一線用藥": {
            "藥物": ["atezolizumab + bevacizumab", "durvalumab + tremelimumab"],
            "單用/併用": "必須併用 [條文：9.69-2-(1)]",
            "PD_L1_條件": "不需檢附報告 [條文：9.69-3-(3)附表]",
            "臨床條件": "Child-Pugh A class [條文：9.69-1-(8)]。未曾接受全身性療法 [條文：9.69-2-(1)]。需具備肝外轉移、大血管侵犯，或經 T.A.C.E. 於12個月內 >= 3 次局部治療失敗紀錄 [條文：9.69-2-(1)]。排除曾器官移植、正在接受免疫抑制藥物、有上消化道出血疑慮且未接受完全治療者 [條文：9.69-2-(1)]。sorafenib、lenvatinib、免疫併用僅得擇一給付 [條文：9.69-2-(1)]。"
        },
        "後續治療 (舊案續用)": {
            "藥物": ["nivolumab"],
            "單用/併用": "單獨使用 [條文：9.69-1]",
            "PD_L1_條件": "不需檢附報告 [條文：9.69-3-(3)附表]",
            "臨床條件": "已使用過至少一線標靶藥物治療失敗。限 109年4月1日前經審核同意用藥，後續評估符合續用申請條件者 [條文：9.69-1-(8)]。"
        }
    },
    "胃癌": {
        "第一線用藥": {
            "藥物": ["nivolumab"],
            "單用/併用": "併用 (與 fluoropyrimidine 及 oxaliplatin 併用) [條文：9.69-2-(5)]",
            "PD_L1_條件": "CPS >= 5 [條文：9.69-3-(3)附表]",
            # 臨床條件加入與 zolbetuximab 僅得擇一使用的限制[cite: 2]
            "臨床條件": "第一線治療晚期或轉移性且不具有 HER2 過度表現的胃癌病人（不含胃腸基質瘤及神經內分泌腫瘤/癌）。與 zolbetuximab 僅得擇一使用，且治療失敗時不可互換 [條文：9.69-2-(5)]。"
        },
        "後線治療 (舊案續用)": {
            "藥物": ["nivolumab"],
            "單用/併用": "單獨使用 [條文：9.69-1]",
            "PD_L1_條件": "CPS >= 1 [條文：9.69-3-(3)附表]",
            "臨床條件": "先前已使用過二線(含)以上化學治療均失敗，限 109年4月1日前經審核同意用藥符合續用者 [條文：9.69-1-(6)]。"
        }
    },
    "大腸直腸癌": {
        "第一線用藥": {
            "藥物": ["pembrolizumab"],
            "單用/併用": "單獨使用 [條文：9.69-1]",
            "PD_L1_條件": "不需檢附報告 [條文：9.69-3-(3)附表]",
            "臨床條件": "做為無法切除或轉移性高微衛星不穩定性(MSI-H)或錯誤配對修復功能不足性(dMMR)大腸直腸癌(CRC)之第一線治療 [條文：9.69-1-(11)]。"
        }
    },
    "食道鱗狀細胞癌": {
        "第一線用藥": {
            "藥物": ["nivolumab"],
            "單用/併用": "併用 (與 fluoropyrimidine 及 cisplatin 或 oxaliplatin 併用) [條文：9.69-2-(8)]",
            "PD_L1_條件": "TC >= 1% [條文：9.69-3-(3)附表]",
            "臨床條件": "無法接受化學放射性治療或手術切除等治癒性治療之晚期或轉移性食道鱗狀細胞癌病人 [條文：9.69-2-(8)]。"
        },
        "第二線用藥": {
            "藥物": ["nivolumab"],
            "單用/併用": "單獨使用 [條文：9.69-1]",
            "PD_L1_條件": "TC >= 1% [條文：9.69-3-(3)附表]",
            "臨床條件": "曾接受合併含鉑及 fluoropyrimidine 化學治療之後惡化的無法切除晚期或復發性病人 [條文：9.69-1-(10)]。"
        }
    },
    "膽道癌": {
        "第一線用藥": {
            "藥物": ["durvalumab"],
            "單用/併用": "併用 (與 cisplatin 及 gemcitabine 併用至多8個療程，接續單用) [條文：9.69-2-(6)]",
            "PD_L1_條件": "不需檢附報告 [條文：9.69-3-(3)附表]",
            # 微調排除條件的字眼，符合新條文「具有或曾有活動性...」[cite: 2]
            "臨床條件": "先前未接受過治療或不可手術之局部晚期或轉移性膽道癌 [條文：9.69-2-(6)]。須排除壺腹癌、曾接受異體器官移植、具有或曾有活動性自體免疫或發炎性疾病 [條文：9.69-2-(6)]。"
        }
    },
    "泌尿道上皮癌": {
        "第一線用藥 (單用)": {
            "藥物": ["pembrolizumab", "atezolizumab"],
            "單用/併用": "單獨使用 [條文：9.69-1]",
            "PD_L1_條件": "pembrolizumab: CPS >= 10; atezolizumab: IC >= 5% (註: atezo限113/8/1前審核同意) [條文：9.69-3-(3)附表]",
            "臨床條件": "轉移性且不適合接受化學治療 [條文：9.69-1-(4)]。需符合聽力受損、周邊神經病變或 CIRS score > 6 條件之一 [條文：9.69-1-(4)]。pembrolizumab 需 eGFR > 30 且 < 60 mL/min/1.73m2 [條文：9.69-3-(2)]。"
        },
        "第一線用藥 (併用)": {
            "藥物": ["nivolumab"],
            "單用/併用": "併用 (與 cisplatin 及 gemcitabine 併用至多6個療程，接續單用) [條文：9.69-2-(9)]",
            "PD_L1_條件": "TC >= 1% [條文：9.69-3-(3)附表]",
            "臨床條件": "無法切除或轉移性泌尿道上皮癌 [條文：9.69-2-(9)]。併用化療需 eGFR >= 60 mL/min/1.73m2 [條文：9.69-3-(2)]。"
        },
        "第二線用藥": {
            "藥物": ["pembrolizumab", "nivolumab", "atezolizumab"],
            "單用/併用": "單獨使用 [條文：9.69-1]",
            "PD_L1_條件": "pembrolizumab: CPS >= 10; nivolumab: TC >= 5%; atezolizumab: IC >= 5% (註: atezo限113/8/1前審核同意) [條文：9.69-3-(3)附表]",
            "臨床條件": "先前已使用過 platinum 類化學治療失敗後疾病惡化的局部晚期無法切除或轉移性患者 [條文：9.69-1-(4)]。eGFR > 30 mL/min/1.73m2 [條文：9.69-3-(2)]。"
        },
        "維持療法": {
            "藥物": ["avelumab"],
            "單用/併用": "單獨使用 [條文：9.69-1]",
            "PD_L1_條件": "不需檢附報告 [條文：9.69-3-(3)附表]",
            "臨床條件": "接受第一線含鉑化學治療4至6個療程後，疾病未惡化且達部分緩解 (PR) 或呈穩定狀態 (SD) [條文：9.69-1-(4)]。eGFR > 30 mL/min/1.73m2 [條文：9.69-3-(2)]。"
        }
    },
    "頭頸部鱗狀細胞癌 (不含鼻咽癌)": {
        "第一線用藥": {
            "藥物": ["pembrolizumab"],
            "單用/併用": "單獨使用 [條文：9.69-1]",
            "PD_L1_條件": "CPS >= 20 [條文：9.69-3-(3)附表]",
            "臨床條件": "先前未曾接受全身性治療且無法手術切除之復發性或轉移性 (第三期或第四期) [條文：9.69-1-(5)]。"
        },
        "第二線用藥": {
            "藥物": ["pembrolizumab", "nivolumab"],
            "單用/併用": "單獨使用 [條文：9.69-1]",
            "PD_L1_條件": "pembrolizumab: TPS >= 50%; nivolumab: TC >= 10% [條文：9.69-3-(3)附表]",
            "臨床條件": "先前已使用過 platinum 類化學治療失敗後，又有疾病惡化的復發性或轉移性 (第三期或第四期) [條文：9.69-1-(5)]。"
        }
    },
    "黑色素瘤": {
        "晚期/轉移性": {
            "藥物": ["pembrolizumab", "nivolumab"],
            "單用/併用": "單獨使用 [條文：9.69-1]",
            "PD_L1_條件": "不需檢附報告 [條文：9.69-3-(3)附表]",
            "臨床條件": "腫瘤無法切除或轉移之第三期或第四期，先前曾接受過至少一次全身性治療失敗者 [條文：9.69-1-(1)]。需檢附 BRAF 腫瘤基因檢測結果 [條文：9.69-3-(7)]。"
        }
    },
    "早期三陰性乳癌": {
        "術前前導至術後輔助": {
            "藥物": ["pembrolizumab"],
            "單用/併用": "併用接單用 (前導：與 carbo/paclitaxel 併用至多4療程 -> 加上 cyclo/doxo 或 epirubicin 併用至多4療程；輔助：單用至多9療程) [條文：9.69-2-(7)]",
            "PD_L1_條件": "不需檢附報告 [條文：9.69-3-(3)附表]",
            # 臨床條件加入 pembrolizumab 與 olaparib 僅能擇一支付的限制[cite: 2]
            "臨床條件": "非轉移性、第II期至第IIIb期成年病人 [條文：9.69-2-(7)]。初次申請需檢附 ER、PR 及 HER2 為陰性之檢測報告 [條文：9.69-3-(7)]。術後輔助治療須為術前治療後未達 pCR 者，且須檢附 non-pCR 佐證。用於術後輔助治療，pembrolizumab 與 olaparib 僅能擇一支付 [條文：9.69-2-(7), 9.69-3-(9)]。"
        }
    },
    "小細胞肺癌": {
        "擴散期": {
            "藥物": ["atezolizumab", "durvalumab"],
            "單用/併用": "併用 (atezo + carbo + etoposide; 或 durva + etoposide + carbo/cis) [條文：9.69-2-(3)]",
            "PD_L1_條件": "不需檢附報告 [條文：9.69-3-(3)附表]",
            "臨床條件": "適用於先前未曾接受化療，且無腦部或無脊髓轉移之擴散期 (extensive stage) 小細胞肺癌 [條文：9.69-2-(3)]。"
        }
    },
    "惡性肋膜間皮瘤": {
        "第一線用藥": {
            "藥物": ["ipilimumab + nivolumab"],
            "單用/併用": "必須併用 [條文：9.69-2-(4)]",
            "PD_L1_條件": "不需檢附報告 [條文：9.69-3-(3)附表]",
            "臨床條件": "無法切除之惡性肋膜間皮瘤且病理組織顯示為非上皮型 (Non-epithelioid) 病人的第一線治療 [條文：9.69-2-(4)]。"
        }
    },
    "典型何杰金氏淋巴瘤": {
        "復發或惡化": {
            "藥物": ["pembrolizumab", "nivolumab"],
            "單用/併用": "單獨使用 [條文：9.69-1]",
            "PD_L1_條件": "不需檢附報告 [條文：9.69-3-(3)附表]",
            "臨床條件": "先前已接受自體造血幹細胞移植 (HSCT) 與移植後 brentuximab vedotin (BV) 治療，但又復發或惡化 [條文：9.69-1-(3)]。"
        }
    },
    "晚期腎細胞癌": {
        "後線治療": {
            "藥物": ["nivolumab"],
            "單用/併用": "單獨使用 [條文：9.69-1]",
            "PD_L1_條件": "不需檢附報告 [條文：9.69-3-(3)附表]",
            "臨床條件": "先前已使用過至少二線標靶藥物治療均失敗，又有疾病惡化。病理上為亮細胞癌 (clear cell renal carcinoma) [條文：9.69-1-(7)]。"
        }
    },
    "默克細胞癌": {
        "轉移性": {
            "藥物": ["avelumab"],
            "單用/併用": "單獨使用 [條文：9.69-1]",
            "PD_L1_條件": "不需檢附報告 [條文：9.69-3-(3)附表]",
            "臨床條件": "先前已使用過 platinum 類化學治療失敗後，又有疾病惡化之轉移性第四期默克細胞癌 [條文：9.69-1-(9)]。"
        }
    }
}

def format_citation(text):
    """使用正規表達式將 和 [條文：XXX] 轉換為美化的 Markdown 標籤"""
    if not text:
        return ""
    text = re.sub(r'\+)\]', r'**[健保給付規定第 \1 項]**', text)
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

    # [重要排除條件與提醒] 更新全域給付提醒及標靶藥物合併限制[cite: 2]
    st.warning(
        "**⚠️ 全域給付重要提醒 & 排除條件**\n"
        "1. **給付時程期限**：原則上自初次處方用藥日起算 **2 年**（例外：durvalumab 用於非小細胞肺癌鞏固治療為 1 年；pembrolizumab 用於早期三陰性乳癌至多 17 個療程）。\n"
        "2. **互換與合併限制**：各適應症限給付一種 ICI 藥物，且**不得互換**。治療期間**不可合併申報標靶藥物**（例外：atezolizumab+bevacizumab 用於 HCC/NSCLC 一線併用；enfortumab vedotin 用於泌尿道上皮癌三線；cetuximab 用於頭頸部鱗癌等除外）。\n"
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