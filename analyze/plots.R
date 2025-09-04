library(data.table)
library(ggplot2)
library(scales)
library(patchwork)
base_dir = "./docs"
data_dir = "data"
fig_dir = "figs"
bench_data_dir = "benchmarks2025_09_02_H12_M31_S34_05501bb21061f6073fb6ae79820f5e3efd94f6467a4fef329d7be3afeaeaadad"
data_path = file.path(base_dir, data_dir, bench_data_dir)
graph_path = file.path(base_dir, fig_dir, paste0("figs_",bench_data_dir))
if (!dir.exists(graph_path)) {
 dir.create(graph_path)
}
perf_files = list.files(data_path, full.names = TRUE, pattern = "*.csv")
perf_lst = lapply(perf_files, \(x) {
  ret = fread(x)
  name_split = strsplit(basename(x), "_")[[1]]
  ad_name = name_split[length(name_split) - 1]
  test_name = paste0(name_split[1:(length(name_split) - 2)], collapse = "_")
  ret[, ad_name := ad_name]
  ret[, perf_name := test_name]
  return(ret)
})
perf_dt = rbindlist(perf_lst)
setkey(perf_dt, ad_name, perf_name, N)
perf_dt = perf_dt[!grepl("_mean|_median|_stddev|_cv", name)]
perf_dt[, num_ad := as.numeric(strsplit(name, "/")[[1]][2]),.I]
perf_dt[grepl("stan_varmat", name), ad_name := "stan_soa"]
perf_dt[ad_name == "stan", ad_name := "stan_aos"]
summary_dt = perf_dt[, .(mean_cpu = mean(cpu_time), sd_cpu = sd(cpu_time), median_cpu = median(cpu_time), perf_name = perf_name[1], num_ad = num_ad[1]), .(ad_name, name)]
perf_names = summary_dt[, unique(perf_name)]
all_ad_names = summary_dt[, sort(unique(ad_name))]
summary_dt[, ad_name := factor(ad_name, levels = all_ad_names)]
for (graph_perf_name in perf_names) {
  sub_perf_dt = summary_dt[perf_name == graph_perf_name]
  if (stringr::str_count(graph_perf_name, "_") == 0) {
    pretty_graph_name = stringr::str_to_title(graph_perf_name)
  } else if (stringr::str_count(graph_perf_name, "_") == 1) {
    pretty_graph_name = stringr::str_replace_all(graph_perf_name, "_", " ")
    pretty_graph_name = stringr::str_to_title(pretty_graph_name)
  } else {
    pretty_graph_name = graph_perf_name
  }
  perf_plot = ggplot(sub_perf_dt, aes(x = num_ad, y = mean_cpu, color = ad_name)) +
    geom_ribbon(aes(group = ad_name,
      x = num_ad, ymin = mean_cpu - 2*sd_cpu,
      ymax = mean_cpu + 2*sd_cpu),
      fill = "grey60", inherit.aes = FALSE) +
    geom_line() +
    geom_point() +
    scale_y_log10(
      labels = label_number(scale_cut = cut_short_scale(), suffix = " ns"), n.breaks = 5
    ) +
    scale_x_log10(
      labels = label_number(scale_cut = cut_short_scale())
    ) +
    labs(
      x = "N",
      y = "",
      color = "AD Library"
    ) +
    ggtitle("Time (ns)") +
    theme_bw() +
    theme(plot.title = element_text(hjust = 0.5))
  setkey(sub_perf_dt, perf_name, ad_name, num_ad)
  sub_perf_dt[, rel_mean_cpu_time := mean_cpu / sub_perf_dt[ad_name == "baseline", mean_cpu]]
  sub_perf_dt[, rel_p2sd_cpu_time := (mean_cpu + 2 * sd_cpu) / (sub_perf_dt[ad_name == "baseline", mean_cpu] + 2 * sub_perf_dt[ad_name == "baseline", sd_cpu])]
  sub_perf_dt[, rel_m2sd_cpu_time := (mean_cpu - 2 * sd_cpu) / (sub_perf_dt[ad_name == "baseline", mean_cpu] - 2 * sub_perf_dt[ad_name == "baseline", sd_cpu])]
  rel_perf_plot = ggplot(sub_perf_dt,
    aes(x = num_ad, y = rel_mean_cpu_time, color = ad_name)) +
    geom_line() +
    geom_point() +
    scale_y_log10(
      labels = label_number(scale_cut = cut_short_scale(), suffix = " x"), n.breaks = 5
    ) +
    scale_x_log10(
      labels = label_number(scale_cut = cut_short_scale())
    ) +
    labs(
      x = "N",
      y = "",
      color = "AD Library"
    ) +
    ggtitle("Slowdown Relative to Baseline") +
    theme_bw() +
    theme(plot.title = element_text(hjust = 0.5))
  combined_plot = perf_plot +
    rel_perf_plot &
    theme(legend.position = "bottom")
  combined_plot = combined_plot +
    plot_annotation(title = pretty_graph_name) +
    plot_layout(guides = "collect")
  print(combined_plot)
  ggsave(plot = combined_plot, filename =
      file.path(graph_path, paste0(sub_perf_dt[, perf_name[1]],"_plot.png")),
    width = 9, height = 5.5, dpi = 180, units = "in")
  readline("Press [ENTER] to Continue")
}

graph_files = list.files(graph_path, full.names = TRUE, pattern = "*.csv")
