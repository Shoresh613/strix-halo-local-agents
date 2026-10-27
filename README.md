# Local coding agents on Strix Halo (128 GB): what actually works

I've got a mini PC with an AMD Ryzen AI Max+ 395 and 128 GB of unified memory, and wanted to see how close I could get to a capable coding agent that runs entirely at home. I spent over a week throwing models, engines and agent frameworks at it. This page is what survived.

**Update, October 26, 2026:** The first version concluded that large local models weren't worth the extra waiting time for coding-agent work. Then I discovered Qwen3.8 Flash-Next GSQ-RCO. Apparently, the model I was looking for already existed. I just hadn't downloaded it.

**Update, October 27, 2026:** I switched the machine to performance mode, tested IQ3_S alongside IQ2_XS, and tried Pi Coding Agent against OpenCode. Generation speeds almost doubled, the larger models became much more practical, and my original conclusion about memory bandwidth needed revisiting.

**Spoiler alert:** Being able to run 181B-class models locally does help. And apparently, so does turning off low-power mode ;-)

## TL;DR

1. **Small-active MoE + MTP remains the speed sweet spot.** Qwen3.6-35B-A3B-MTP reaches \~81 tok/s on short prompts, handles tools and images, supports 256K context, and fixes bounded bugs in about a minute. Its performance-mode agent median is **63.1 tok/s**.

2. **Bigger models deliver better architectural judgment.** Qwen3.8 Flash-Next IQ2_XS originally scored **20/24 in 57m32s** on a deep review and self-audit, versus Qwen3.6 medium's **14/24 in 29m52s**. New performance-mode tests scored **19/24** with both IQ2_XS and IQ3_S in OpenCode, and **20/24** with IQ3_S in Pi, all in less than 30 minutes.

3. **Performance mode changes the experience.** Qwen3.8 IQ2_XS's observed agent-generation median increased from **15.5 to 31.2 tok/s**. That isn't a controlled power-mode-only comparison, but it makes my earlier performance conclusions look decidedly pessimistic.

4. **Memory bandwidth matters, but isn't the whole story.** 128 GB determines which models fit. Effective bandwidth, GPU clocks, power limits and inference efficiency influence how fast they run. The same nominal 256 GB/s memory bus delivered very different observed speeds.

5. **More quantization precision doesn't guarantee better results.** IQ3_S consumes substantially more memory than IQ2_XS, but both scored 19/24 in the new OpenCode tests.

6. **Context helps agents finish; it doesn't guarantee good judgment.** Raising Qwen3.6 to 256K avoided compaction. Serena improved navigation. Neither eliminated questionable architectural conclusions. The best improvement came from using a stronger model and asking it to audit its own work.

## The rig

|                 |                                                                                              |
| --------------- | -------------------------------------------------------------------------------------------- |
| Price           | 17,500 SEK (\~$1,750) for the entire computer                                                |
| Machine         | AMD Ryzen AI Max+ 395 · Radeon 8060S iGPU (gfx1151) · XDNA 2 NPU                             |
| Memory          | 128 GB LPDDR5X-8000, 256-bit, 256 GB/s theoretical                                       |
| OS              | Ubuntu 26.04, kernel 7.0                                                                     |
| GPU memory      | 512 MB BIOS VRAM carve-out; approximately 116 GiB of shared GPU memory (GTT)                 |
| Inference       | Lemonade → llama.cpp ROCm/Vulkan; FastFlowLM on NPU                                          |
| Agents          | OpenCode 2, Pi Coding Agent, Aider, Hermes Agent                                     |
| Navigation      | Serena and GitNexus (MCP)                                                                    |
| Test repository | Django + React application, 74 MB of source and 2,863 tracked files in the original snapshot |

The original B+C experiments used **low-power mode and OpenCode Build**. The October 27 experiments used **performance mode**, OpenCode 2.2.0 or Pi, and a development branch with ongoing changes.

Those are different experimental conditions, not a clean before-and-after benchmark.

## How I tested

Agent tests used a real Django + React codebase.

**A** asked for a quick project summary. **B** demanded a deep, source-backed architecture review tracing at least two complete UI → backend → UI execution flows. **C** asked the agent to challenge its own findings.

<details>
<summary>Test B — architecture review prompt</summary>

```text
Perform a deep architecture analysis of this repository. Do not rely solely on filenames or directory structure.

Read the actual source code of the key backend and frontend modules, trace at least two complete execution flows from UI to backend and back, identify architectural weaknesses and technical debt, and provide concrete recommendations with file paths and line references.

Clearly distinguish verified findings from hypotheses. Do not modify any files.
```

</details>

<details>
<summary>Test C — self-audit prompt</summary>

```text
Critically audit your previous architecture analysis. Your task is to DISPROVE your own findings wherever possible.

Pay particular attention to authentication, CSRF, offline caching, and asynchronous AI tasks.

Do not modify any files.
```

</details>

Later C runs used more explicit instructions to verify each finding, seek counterevidence and revise unsafe recommendations.

Each report received **0–3 points on four criteria**, for a maximum of 12. For B: project understanding, execution-flow completeness, source verification and actionable recommendations. For C: following the audit task, evidence and counterevidence, self-correction and revised recommendations.

The combined score is out of **24**.

These are subjective assessments of individual reports and visible tool histories, not independently verified correctness rates. Some runs also differed in tool availability, prompts and Git revision. A one-point difference is not statistically meaningful.

## 1. The model lineup

Two speeds matter here:

- **Short-prompt speed:** A quick generation test with limited context.
- **Agent-session speed:** Generation during real coding-agent work, with growing context, thinking tokens and tool interactions.

The table below preserves the original **low-power** measurements. The agent figures are journal medians for requests generating at least 100 tokens.

| Model                          | Quantization / size              | Short prompt tok/s | Agent median tok/s | Observation                                      |
| ------------------------------ | -------------------------------- | -----------------: | -----------------: | ------------------------------------------------ |
| **Qwen3.6-35B-A3B-MTP**        | UD-Q4_K_XL, 22 GB                |             **81** | **34** (837 calls) | Fast daily driver, tools, vision, 256K context   |
| GLM-4.7-Flash (30B-A3B)        | Q4_K_M, \~18 GB                  |                 70 |                  — | Good bounded coding performance                  |
| gpt-oss-120b                   | MXFP4, 59 GB                     |               \~48 |            31 (57) | Fast for its size; disappointing agent tool use  |
| Qwen3-Coder-Next (80B-A3B)     | Q8_0                             |                  — |            27 (34) | Thorough reading; weak architectural conclusions |
| **Qwen3.8 Flash-Next GSQ-RCO** | **IQ2_XS, \~68 GB + MTP/vision** |                  — |     **15.5** (385) | Best original deep-review result                 |
| Qwen3.8 Flash-Next             | Q2_0, \~66 GB + MTP              |                  — |         10.6 (200) | Similar review quality, slower                   |
| Gemma-4-31B-it-MTP             | \~19 GB                          |                  — |            26 (28) | Used for image tasks                             |
| MAI-Code-1.1-Flash             | Q2-XS + DFlash, 53 GB            |                  — |            23 (88) | No improvement on broad reviews                  |
| Qwen3.8 coder-pruned           | IQ1_M, \~85 GB in RAM            |              16–22 |           17 (110) | Deep review took 51 minutes                      |
| DeepSeek-V4-Flash              | IQ2_XXS, 81 GB                   |                  — |             6 (83) | B stopped after 62 minutes                       |
| Qwen3.6 on the NPU             | FastFlowLM                       |              13–16 |             6 (27) | Around 5× slower than the iGPU                   |
| Qwen3.5-4B on the NPU          | FastFlowLM                       |                  — |            43 (20) | Useful as a small helper                         |

The original Qwen3.8 figures came from the October 24–25 journal sample, including exploratory calls and retries as well as scored tests.

### Why Strix Halo is interesting

The attraction is memory capacity.

Ordinary discrete GPUs can be much faster, but they typically have far less memory. Strix Halo gives the integrated GPU access to most of the machine's 128 GB unified-memory pool.

Its nominal bandwidth is **256 GB/s**, compared with approximately 1,008 GB/s for an RTX 4090 and 1,792 GB/s for an RTX 5090.

That is the trade-off: the Strix Halo can load much larger models than a typical consumer GPU, while a high-end card runs models that fit in its VRAM much faster.

The large Qwen3.8 model is especially interesting because it is a Mixture-of-Experts architecture with roughly 6B active parameters per token, despite its much larger total parameter count.

It also has a substantial **N-gram component**, which uses learned token-sequence lookups rather than simply adding more conventional neural computation.

The result is a large model that can run on this hardware at useful, if not cloud-like, speeds.

## 2. Performance mode: the biggest new finding

The original article was based almost entirely on low-power operation.

On October 27, I collected new Lemonade telemetry while running performance-mode agent sessions.

### Observed generation speed

| Model              | Low-power median | Performance median | Change |
| ------------------ | ---------------: | -----------------: | -----: |
| Qwen3.6 35B MTP    |         34 tok/s |     **63.1 tok/s** |   +86% |
| Qwen3.8 IQ2_XS MTP |       15.5 tok/s |     **31.2 tok/s** |  +101% |
| Qwen3.8 IQ3_S MTP  |                — |     **28.1 tok/s** |      — |

The performance-mode journal sample:

| Model          | Calls | Output tokens | Mean tok/s | Median tok/s | Aggregate tok/s |
| -------------- | ----: | ------------: | ---------: | -----------: | --------------: |
| Qwen3.6 35B    |    59 |        16,441 |       62.6 |     **63.1** |            61.1 |
| Qwen3.8 IQ2_XS |    61 |        21,880 |       30.2 |     **31.2** |            26.1 |
| Qwen3.8 IQ3_S  |    59 |        35,571 |       28.1 |     **28.1** |            23.4 |

*Aggregate speed = total output tokens divided by total generation time. The mean and median are calculated across individual calls.*

The difference is substantial enough to change the practical assessment of the machine.

Qwen3.8 at approximately **30 tok/s during agent work** feels very different from the same family at approximately 15 tok/s.

## 3. MTP: I tuned for an evening and landed on the default

MTP (multi-token prediction) lets a small draft head propose upcoming tokens that the main model can verify together.

On Qwen3.6, it made a substantial difference.

In a controlled probe with temperature 0, seed 42 and 384 output tokens, enabling MTP increased speed from **49 to 70 tok/s (+42%)**, with roughly 59–68% of proposed tokens accepted.



I then tested draft lengths from 1 to 8.

Three won at approximately **81 tok/s**, consistent across three runs. Increasing the draft length to eight made generation 32% slower. A length of six, recommended in some guides, was 14% slower than three.

Three is also llama.cpp's default.

An evening of tuning to confirm the default. I'll call that validation.

I also tested `--spec-draft-p-min`, which stops speculative drafting when confidence falls:

| p-min | 0 (default) | 0.10 | 0.60 | 0.75 | 0.90 |
| ----- | ----------: | ---: | ---: | ---: | ---: |
| tok/s |    **80.7** | 73.2 | 56.8 | 61.9 | 53.4 |

Again, the default won.

MTP is however not universally beneficial. On GLM-4.7-Flash it reduced speed from **70 to 49 tok/s**.

And short-prompt speed is not what an agent sustains with a large context.

## 4. Parallel agents: more hands, same shared resources

I wanted several local agents working in parallel.

The memory bus had other plans.

These original low-power measurements used GLM-4.7-Flash Q8, with each request adding 2,048 tokens to an existing context.

| Context | Backend | One stream: tok/s / first token | Two streams: tok/s per stream / first token |
| ------- | ------- | ------------------------------- | ------------------------------------------- |
| 32K     | ROCm    | 23.9 / 23 s                     | 9.9 / 88 s                                  |
| 64K     | ROCm    | 9.3 / 48 s                      | 4.3 / 197 s                                 |
| 128K    | ROCm    | 6.1 / 97 s                      | 2.4 / 377 s                                 |
| 64K     | Vulkan  | 12.5 / 42 s                     | 1.5 / 84 s                                  |

With short prompts, eight simultaneous requests achieved **166 tok/s in total**, approximately 21 tok/s per agent rather than 70 when running alone.

But in a real OpenCode session, two subagents at 39K and 62K context crawled at **0.9–1.3 tok/s**.

Long context also increased time to first token dramatically.

ROCm generally handled two long streams better than Vulkan in these experiments, although Vulkan sometimes returned the first token faster.

Performance mode would likely improve these numbers, but the shared-resource trade-off remains. For my local workflows, serial or no subagents are usually easier to manage.

## 5. Can the agents actually finish useful work?

Raw generation speed is only half the story.

### Bounded fixes: surprisingly good

A deliberately reintroduced single-file regression was fixed by **Qwen3.6 + OpenCode in 50–90 seconds**, passing 3/3 public and 13/13 held-out tests.

Aider completed the same type of task in 95 seconds, and GLM-4.7-Flash in 112 seconds.

This is where small, fast local coding models shine.

### General autonomous tasks: less impressive

In a scheduled Hermes task involving web research and document creation, gpt-oss-120b reported success despite stale or broken links and incorrect tool use.

Another model spent **76 minutes and 45 calls** on the task without producing the requested document.

The issue wasn't writing fluent text. It was reliably planning, executing and completing the workflow.

### Early broad reviews: convincing reports, weak evidence

In the initial architecture-review round:

| Model                      | Test B time |
| -------------------------- | ----------: |
| gpt-oss-120b               |       4m31s |
| Qwen3-Coder-Next 80B Q8    |       9m23s |
| Qwen3.8 coder-pruned IQ1_M |      51m26s |

The reports looked plausible, but contained unsupported architectural claims.

The models were good at finding and describing code. Proving their conclusions was harder.

### The controlled short-context rerun

I also tried broad reviews on a frozen repository revision, with OpenCode 2.x, 32K–64K context and a 15-minute limit.

**None of the local models completed the review independently within the limit.**

That included Qwen3.6 with and without code-navigation tools, MAI-Code, GLM-4.7-Flash and DeepSeek.

When forced to stop and summarize, Qwen3.6 scored 5.5/12 and GLM 4/12.

A cloud frontier model (Sol 6.1) completed the same review in 6 minutes and met all eight evaluation points in that particular comparison.

The local agents' main problem was often context management. They filled the available window with code and search results, compacted their history, then reread material they had already examined.

In some runs, **17–42% of source lines read were repeats**. In the 32K runs, 74–81% of model output could be consumed by summarizing its own history.

Not ideal.

### The 256K retest

Increasing Qwen3.6's context to **256K** and output limit to **32K** finally allowed it to complete B+C without compaction.

It took **29m52s** at medium thinking and scored **14/24**.

By the end, OpenCode reported 237,519 tokens in context, about 91% of the available window.

The self-audit was useful. It corrected several findings and reconsidered recommendations.

But the model still confused missing references with unused code and suggested risky architectural changes without sufficient evidence.

**More context solved a workflow problem, not a judgment problem.**

### Serena and GitNexus: useful navigation, not automatic correctness

An explicit MCP-assisted rerun used Serena to navigate symbols and inspect project memories.

That improved code discovery, but the architecture report still scored **6/12**, the same as the earlier review.

It was also slower: **22m46s versus 11m54s**, although tool availability, retries and loaded project memories differed.

## 6. The bigger model: a real improvement

Qwen3.8 Flash-Next GSQ-RCO IQ2_XS changed my view of large local models.

The original low-power B+C tests produced much better architectural assessments than Qwen3.6, including stronger self-audits and more careful handling of backward compatibility.

### Original low-power results

| Model / thinking              |      B |      C |      Total |     Score |
| ----------------------------- | -----: | -----: | ---------: | --------: |
| Qwen3.6 medium                |  11:54 |  17:58 |  **29:52** |     14/24 |
| Qwen3.6 high                  |  15:16 |  29:00 |  **44:16** |     10/24 |
| Qwen3.8 IQ2_XS low            |  24:43 |  29:46 |  **54:29** |     18/24 |
| Qwen3.8 IQ2_XS medium, first  |  33:47 |  23:45 |  **57:32** | **20/24** |
| Qwen3.8 IQ2_XS medium, second |  26:15 |  47:00 |  **73:15** |     19/24 |
| Qwen3.8 IQ2_XS high           | \~1h16 | \~1h07 | **\~2h23** |     20/24 |
| Qwen3.8 Q2_0 medium           |  \~64m |  43:23 | **\~1h47** |     19/24 |



*OpenCode Build, low-power mode. Scores are subjective; test conditions and tool status varied.*

The first IQ2_XS medium run scored **20/24 in 57m32s**, compared with Qwen3.6 medium's 14/24.

The difference was not just more detailed reporting. Qwen3.8 was better at distinguishing actual problems from deliberate engineering decisions.

It also performed a better self-audit.

High thinking took much longer without a clear quality improvement. The same pattern appeared with Qwen3.6.

**Medium thinking offered the best balance in my tests.**

## 7. The new tests: IQ2_XS, IQ3_S and Pi

The October 27 experiments added a higher-precision quantization, a new agent framework and the higher power setting.

### IQ2_XS versus IQ3_S

Both quantizations use the same basic Qwen3.8 Flash-Next architecture.

| Component          |      IQ2_XS |         IQ3_S |
| ------------------ | ----------: | ------------: |
| Main model weights |   \~39.2 GB |     \~54.8 GB |
| N-gram component   |   \~28.8 GB |     \~28.8 GB |
| Main model files   | **\~68 GB** | **\~83.6 GB** |
| Separate MTP head  |    \~4.1 GB |      \~4.1 GB |

The N-gram component supplies learned representations for token sequences. It is part of the trained model, not the same thing as MTP-based speculative decoding.

IQ3_S used approximately **117 GB of RAM** in one run, so it fits on the Strix Halo but leaves limited headroom.

In the new Lemonade logs, IQ2_XS also generated slightly faster than IQ3_S: **31.2 versus 28.1 tok/s median**.

So what about quality?

### Performance-mode B+C results

| Model / agent           |         B |         C | Total time |     Score |
| ----------------------- | --------: | --------: | ---------: | --------: |
| IQ3_S · OpenCode 2.2.0  |     11:51 |     12:53 |  **24:44** |     19/24 |
| IQ2_XS · OpenCode 2.2.0 |     16:36 |     18:52 |  **35:28** |     19/24 |
| IQ3_S · Pi              | Completed | Completed | Not logged | **20/24** |

*Medium thinking. The IQ2_XS C run included extra context-reading overhead after an intervening session. Pi doesn't record a comparable total runtime in my setup.*

The IQ3_S OpenCode run was faster overall even though IQ2_XS had slightly better generation throughput in the journal sample.

That illustrates why **agent wall-clock time cannot be predicted from tok/s alone**. The number of generated tokens, tool calls, context processing and exploration decisions all matter.

And despite IQ3_S's higher precision, both OpenCode configurations scored **19/24**.

There is no clear evidence here yet that the larger quantization delivers better reasoning quality, though it is very likely and has scored better in benchmarks.

### Pi Coding Agent

A LinkedIn commenter suggested trying Pi with IQ3_S.

Its first B+C run scored **20/24**.

Pi took a somewhat different approach from OpenCode, explored more of the legacy architecture and identified a plausible bug in an older workflow (9/12).

Its self-audit then corrected several of its own assumptions and reconsidered recommendations that could break existing functionality (11/12).

**One point does not make Pi the winner**, especially when the agents followed different execution flows. But it performed well enough to deserve more systematic testing.

### Why self-auditing matters

Across these tests, models have withdrawn or revised claims about missing CI coverage, duplicated code, security vulnerabilities, API compatibility and billing behavior.

Some original recommendations would have removed data still required by deployed clients or introduced risky refactors.

The self-audit often caught those mistakes.

A convincing architecture review is useful. A review that can survive a serious attempt to disprove it is much more valuable.

## What I'd do today

**For quick coding tasks:** Qwen3.6-35B-A3B-MTP with llama.cpp ROCm. It's fast, handles tools well, and has enough context for most normal work.

**For deep architecture reviews:** Qwen3.8 IQ2_XS or IQ3_S at medium thinking. IQ2_XS offers more memory headroom; IQ3_S is worth further testing, but hasn't demonstrated a clear quality advantage.

**For agents:** OpenCode remains my baseline. Pi is a promising minimalistic alternative.

**For reliability:** Ask for counterevidence, and check consequential recommendations before implementing them. Local models at this size aren't there yet.

**For performance:** Use performance mode when speed matters. The improvement in my new measurements was much larger than expected.

**For configuration:** Avoid assuming that more manual llama.cpp flags are better. Keep track of what actually changed between runs. I also recommend a sufficiently large agent output limit — I used 32K — because thinking and compaction can exhaust small output budgets.

**For parallelism:** Prefer serial subagents on this machine when contexts are long. Multiple agents compete for the same shared resources.

## Getting started

My local inference stack is Lemonade with llama.cpp ROCm.

```bash
# Install Lemonade
sudo add-apt-repository ppa:lemonade-team/stable
sudo apt install lemonade-server

# Install the GPU and optional NPU backends
lemonade backends install llamacpp:rocm
lemonade backends install flm:npu

# Fast daily-driver model
lemonade pull Qwen3.6-35B-A3B-MTP-GGUF
```

For Qwen3.8 IQ2_XS with MTP and vision:

```bash
lemonade pull user.Qwen38-IQ2XS-MTP \
  --checkpoint main ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF:IQ2_XS \
  --checkpoint draft ggml-org/Qwen3.8-Flash-Next-GGUF:mtp-Qwen3.8-Flash-Next-Q8_0.gguf \
  --checkpoint mmproj ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF:mmproj-Qwen3.8-Flash-Next-BF16.gguf \
  --recipe llamacpp \
  --label mtp \
  --label vision \
  --label reasoning \
  --label tool-calling
```

For IQ3_S with MTP, without vision:

```bash
lemonade pull user.Qwen38-IQ3S-MTP \
  --checkpoint main ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF:IQ3_S \
  --checkpoint draft ggml-org/Qwen3.8-Flash-Next-GGUF:mtp-Qwen3.8-Flash-Next-Q8_0.gguf \
  --recipe llamacpp \
  --label mtp \
  --label reasoning \
  --label tool-calling
```

My Qwen3.6 configuration uses a 256K context window and MTP with three draft tokens:

```bash
lemonade load Qwen3.6-35B-A3B-MTP-GGUF \
  --llamacpp rocm \
  --ctx-size 262144 \
  --save-options \
  --llamacpp-args "--parallel 1 --spec-type draft-mtp --n-predict 32768"
```

The coding agents connect to Lemonade's OpenAI-compatible endpoint at `http://localhost:13305/api/v1`.

The commands reflect my tested setup; exact options and checkpoint availability can change between Lemonade versions.

## Final thoughts

For 17,500 SEK, this computer can run models that simply wouldn't fit on most consumer GPUs (though strata according to a LinkedIn commenter reportedly makes it possible to run both IQ2 and IQ3 on 20GB VRAM + 64GB RAM at 40 tokens/second on a 4000 RTX Ada).

Qwen3.6 is fast enough for everyday coding. Qwen3.8 is capable enough to produce useful deep architecture reviews, provided its conclusions are checked.

The new tests changed two of my assumptions.

First, **large local models don't have to be quite as slow as my original low-power measurements suggested**.

Second, memory bandwidth alone doesn't explain performance. The actual power configuration, GPU behavior, inference engine and agent workflow matter too.

But the most important lesson hasn't changed:

**Tokens per second measures how fast a model talks. It doesn't measure how well an agent works.**

For that, I care more about whether it completes the task, supports its claims with source code, and recognizes when its own recommendations are wrong.

That's where these local models are finally getting interesting.

---

*These are exploratory, mostly single-run measurements rather than a controlled leaderboard. Scores are subjective, generation rates include thinking tokens, and the low-power and performance-mode samples differ in more than the power setting. Original experimental data and plotting scripts are available in [`data/`](data/) and [`scripts/`](scripts/).*
