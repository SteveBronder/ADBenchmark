library(data.table)
library(ggplot2)
library(scales)
library(patchwork)
perf_files = list.files("./docs/data/benchmark_aggs", full.names = TRUE)
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
    ggtitle("Speedup Relative to Baseline") +
    theme_bw() +
    theme(plot.title = element_text(hjust = 0.5))
  combined_plot = perf_plot +
    rel_perf_plot &
    theme(legend.position = "bottom")
  combined_plot = combined_plot +
    plot_annotation(title = pretty_graph_name) +
    plot_layout(guides = "collect")
  print(combined_plot)
  ggsave(plot = combined_plot, filename = paste0("./docs/figs/combined_", sub_perf_dt[, perf_name[1]],"_plot.png"),
    width = 9, height = 5.5, dpi = 180, units = "in")
  readline("Press Enter to Continue")
}

