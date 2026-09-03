import re

file_path = r'c:\Users\HP\Desktop\Process Optimisation\Epoxy_myselate.py'
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

# We need to remove the block from inside the loop
start_str = '''        # Moved Upload Documents immediately below the Reaction Scheme
        st.subheader("📄 Upload Documents")'''
        

end_str = '''                            st.write(f"Final yield: {calc_yield:.2f}% (Calculated)")
                    except Exception:
                        pass'''

start_idx = text.find(start_str)
end_idx = text.find(end_str) + len(end_str)

if start_idx != -1 and end_idx != -1:
    block_to_remove = text[start_idx:end_idx]
    
    # We will remove it and add a new global version below the loop
    text = text[:start_idx] + text[end_idx:]
    
    # We will insert the global version right before 'st.header("🤖 AI Analysis & Chat")'
    ai_header_idx = text.find('st.header("🤖 AI Analysis & Chat")')
    
    global_block = '''    st.markdown("---")
    st.subheader("📄 Upload Global Process Document (ROS)")
    uploaded_ros_file = st.file_uploader("Upload ROS PDF (Applies to entire process)", type=["pdf"], key="global_ros_up")

    if uploaded_ros_file:
        if "global_last_ros_file" not in st.session_state or st.session_state.global_last_ros_file != uploaded_ros_file.name:
            st.session_state.global_last_ros_file = uploaded_ros_file.name
            
            with st.spinner("Processing global document..."):
                global_text, global_tables = extract_pdf_with_azure_helper(uploaded_ros_file, "ROS Document")
                
                # Assign to all stages to keep chat/summary logic happy
                for sn in st.session_state.stages:
                    st.session_state.stages[sn]["ros_text"] = global_text
                    st.session_state.stages[sn]["ros_tables"] = global_tables
                    st.session_state.stages[sn]["last_uploaded_ros_file"] = uploaded_ros_file.name

    # Display tables/text once (using Stage 1's copy which is identical to the rest)
    if st.session_state.stages.get("Stage 1", {}).get("ros_tables"):
         with st.expander("View Extracted Tables"):
              st.write("### ROS Tables")
              for idx, df in enumerate(st.session_state.stages["Stage 1"]["ros_tables"]):
                  st.write(f"Table {idx+1}")
                  st.dataframe(df)

    if st.session_state.stages.get("Stage 1", {}).get("ros_text"):
         with st.expander("View Extracted Text"):
              st.write("### ROS Extracted Text")
              st.text(st.session_state.stages["Stage 1"]["ros_text"])

         clean = st.session_state.stages["Stage 1"]["ros_text"].replace("\\n"," ")
         clean = re.sub(r"\\s+"," ",clean).replace("–","-")
         
         if "yield" in clean.lower() or "batch output" in clean.lower():
             st.success("📌 Yield values extracted:")
             batch_input_match = re.search(r"Batch\\s*input[^0-9]*([\\d\\.]+)", clean, re.I)
             batch_output_match = re.search(r"Batch\\s*Output[^0-9]*([\\d\\.]+)", clean, re.I)
             ratio_match = re.search(r"Theoretical\\s*output[^0-9]*1\\s*:\\s*([\\d\\.]+)", clean, re.I)
             direct_theo_match = re.search(r"Theoretical\\s*output[^0-9]*([\\d\\.]+)(?!\\s*:)", clean, re.I)

             if batch_input_match and batch_output_match:
                 try:
                     b_in = float(batch_input_match.group(1))
                     b_out = float(batch_output_match.group(1))
                     st.write(f"Batch Input: {b_in} kg")
                     st.write(f"Batch Output: {b_out} kg")
                     if ratio_match:
                         ratio = float(ratio_match.group(1))
                         theoretical_yield = b_in * ratio
                         actual_yield_percentage = (b_out / theoretical_yield) * 100
                         st.write(f"Theoretical Ratio: 1 : {ratio}")
                         st.write(f"Calculated Theoretical Yield: {theoretical_yield:.2f} kg")
                         st.write(f"**Final Yield:** {actual_yield_percentage:.2f}%")
                     elif direct_theo_match:
                         theo_out = float(direct_theo_match.group(1))
                         if theo_out > 0:
                             actual_yield_percentage = (b_out / theo_out) * 100
                             st.write(f"Theoretical Output: {theo_out} kg")
                             st.write(f"**Final Yield:** {actual_yield_percentage:.2f}%")
                 except Exception as e:
                     st.write(f"Error calculating yield: {e}")
             else:
                 theo = re.search(r"Theoretical[^0-9]*([\\d\\.]+)(?!\\s*:)", clean,re.I)
                 if theo: st.write(f"Theoretical output: {theo.group(1)}")
                 yrange = re.search(r"Yield\\s*Range[^0-9]*([\\d\\.]+)\\s*-\\s*([\\d\\.]+)", clean,re.I)
                 if yrange: st.write(f"Yield range: {yrange.group(1)}–{yrange.group(2)}")
                 actual = re.search(r"Actual[^0-9]*([\\d\\.]+)", clean,re.I)
                 if actual: st.write(f"Actual output: {actual.group(1)}")
                 yield_match = re.search(r"Yield.{0,50}[:=]\\s*(\\d+(?:\\.\\d+)?)\\s*%", clean, re.IGNORECASE)
                 if yield_match:
                     st.write(f"Final yield: {yield_match.group(1)}%")
                 else:
                     try:
                         if theo and actual:
                             t_val = float(theo.group(1))
                             a_val = float(actual.group(1))
                             if t_val > 0:
                                 calc_yield = (a_val / t_val) * 100
                                 st.write(f"Final yield: {calc_yield:.2f}% (Calculated)")
                     except Exception:
                         pass
'''
    text = text[:ai_header_idx] + global_block + "\n\n" + text[ai_header_idx:]

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(text)
print("Done")
