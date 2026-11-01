/* radio.c
 * Build: gcc radio.c -o radio $(pkg-config --cflags --libs gtk4 gstreamer-1.0 libsoup-3.0)
 * Needs gst-plugins-good (souphttpsrc) and gst-plugins-base (playbin) at runtime.
 */
#include <gtk/gtk.h>
#include <gst/gst.h>
#include <libsoup/soup.h>

#define STREAM_URI      "http://stream.live.vc.bbcmedia.co.uk/bbc_world_service"
#define FEED_URI        "https://feeds.bbci.co.uk/news/world/rss.xml"
#define TICKER_CHARS    90      /* visible width of the ticker */
#define TICKER_MS       120     /* scroll speed */
#define REFRESH_SECONDS 300     /* feed refresh interval */
#define SEPARATOR       "   \u2022   "

typedef struct {
  GtkWidget   *ticker_label;
  GtkWidget   *status_label;
  GtkWidget   *play_button;
  GstElement  *playbin;
  guint        bus_watch_id;
  SoupSession *session;
  GCancellable *cancel;
  char        *ticker_text;   /* headlines joined by SEPARATOR */
  glong        ticker_len;    /* length in characters */
  glong        offset;
  guint        tick_id;
  guint        refresh_id;
  gboolean     playing;
} App;

/* ---------- RSS parsing (GMarkup, no libxml needed) ---------- */

typedef struct {
  gboolean in_item, in_title;
  GString *title, *out;
} FeedState;

static void feed_start(GMarkupParseContext *c, const char *name, const char **an,
                       const char **av, gpointer data, GError **err)
{
  FeedState *s = data;
  if (g_str_equal(name, "item")) s->in_item = TRUE;
  else if (s->in_item && g_str_equal(name, "title")) {
    s->in_title = TRUE;
    g_string_truncate(s->title, 0);
  }
}

static void feed_end(GMarkupParseContext *c, const char *name, gpointer data, GError **err)
{
  FeedState *s = data;
  if (g_str_equal(name, "title") && s->in_title) {
    s->in_title = FALSE;
    g_strstrip(s->title->str);
    if (s->title->len) {
      g_string_append(s->out, s->title->str);
      g_string_append(s->out, SEPARATOR);
    }
  } else if (g_str_equal(name, "item")) {
    s->in_item = FALSE;
  }
}

static void feed_text(GMarkupParseContext *c, const char *text, gsize len,
                      gpointer data, GError **err)
{
  FeedState *s = data;
  if (s->in_title) g_string_append_len(s->title, text, len);
}

static char *parse_headlines(const char *xml, gsize len)
{
  static const GMarkupParser parser = { feed_start, feed_end, feed_text, NULL, NULL };
  FeedState st = { FALSE, FALSE, g_string_new(NULL), g_string_new(NULL) };
  GMarkupParseContext *ctx = g_markup_parse_context_new(&parser, 0, &st, NULL);
  gboolean ok = g_markup_parse_context_parse(ctx, xml, len, NULL) &&
                g_markup_parse_context_end_parse(ctx, NULL);
  char *result = (ok && st.out->len) ? g_string_free(st.out, FALSE)
                                     : (g_string_free(st.out, TRUE), NULL);
  g_string_free(st.title, TRUE);
  g_markup_parse_context_free(ctx);
  return result;
}

/* ---------- Ticker ---------- */

static gboolean on_tick(gpointer data)
{
  App *app = data;
  if (!app->ticker_text || app->ticker_len == 0)
    return G_SOURCE_CONTINUE;

  /* Repeat the text until the visible window is always filled */
  GString *buf = g_string_new(app->ticker_text);
  while (g_utf8_strlen(buf->str, -1) < app->offset + TICKER_CHARS)
    g_string_append(buf, app->ticker_text);

  char *window = g_utf8_substring(buf->str, app->offset, app->offset + TICKER_CHARS);
  gtk_label_set_text(GTK_LABEL(app->ticker_label), window);
  g_free(window);
  g_string_free(buf, TRUE);

  app->offset = (app->offset + 1) % app->ticker_len;
  return G_SOURCE_CONTINUE;
}

static void on_feed_done(GObject *src, GAsyncResult *res, gpointer data)
{
  App *app = data;
  GError *err = NULL;
  GBytes *bytes = soup_session_send_and_read_finish(SOUP_SESSION(src), res, &err);

  if (!bytes) {
    if (!g_error_matches(err, G_IO_ERROR, G_IO_ERROR_CANCELLED)) {
      g_warning("Feed fetch failed: %s", err->message);
      if (!app->ticker_text)
        gtk_label_set_text(GTK_LABEL(app->ticker_label), "News headlines unavailable");
    }
    g_clear_error(&err);
    return;
  }

  gsize size;
  const char *xml = g_bytes_get_data(bytes, &size);
  char *text = parse_headlines(xml, size);
  g_bytes_unref(bytes);

  if (text) {
    g_free(app->ticker_text);
    app->ticker_text = text;
    app->ticker_len = g_utf8_strlen(text, -1);
    app->offset = 0;
  }
}

static gboolean refresh_feed(gpointer data)
{
  App *app = data;
  SoupMessage *msg = soup_message_new(SOUP_METHOD_GET, FEED_URI);
  soup_session_send_and_read_async(app->session, msg, G_PRIORITY_DEFAULT,
                                   app->cancel, on_feed_done, app);
  g_object_unref(msg);
  return G_SOURCE_CONTINUE;
}

/* ---------- Audio ---------- */

static gboolean on_bus_message(GstBus *bus, GstMessage *msg, gpointer data)
{
  App *app = data;

  switch (GST_MESSAGE_TYPE(msg)) {
  case GST_MESSAGE_ERROR: {
    GError *err; char *dbg;
    gst_message_parse_error(msg, &err, &dbg);
    g_printerr("Playback error: %s (%s)\n", err->message, dbg ? dbg : "");
    gtk_label_set_text(GTK_LABEL(app->status_label), "Playback error");
    gst_element_set_state(app->playbin, GST_STATE_NULL);
    app->playing = FALSE;
    gtk_button_set_label(GTK_BUTTON(app->play_button), "Play");
    g_error_free(err); g_free(dbg);
    break;
  }
  case GST_MESSAGE_TAG: {
    GstTagList *tags; char *title = NULL;
    gst_message_parse_tag(msg, &tags);
    if (gst_tag_list_get_string(tags, GST_TAG_TITLE, &title)) {
      char *s = g_strdup_printf("Now playing: %s", title);
      gtk_label_set_text(GTK_LABEL(app->status_label), s);
      g_free(s); g_free(title);
    }
    gst_tag_list_unref(tags);
    break;
  }
  case GST_MESSAGE_BUFFERING: {
    int pct;
    gst_message_parse_buffering(msg, &pct);
    if (pct < 100) {
      char *s = g_strdup_printf("Buffering %d%%", pct);
      gtk_label_set_text(GTK_LABEL(app->status_label), s);
      g_free(s);
    } else if (app->playing) {
      gtk_label_set_text(GTK_LABEL(app->status_label), "Live");
    }
    break;
  }
  default:
    break;
  }
  return G_SOURCE_CONTINUE;
}

static void on_play_clicked(GtkButton *button, gpointer data)
{
  App *app = data;
  app->playing = !app->playing;
  gst_element_set_state(app->playbin,
                        app->playing ? GST_STATE_PLAYING : GST_STATE_PAUSED);
  gtk_button_set_label(button, app->playing ? "Pause" : "Play");
  gtk_label_set_text(GTK_LABEL(app->status_label), app->playing ? "Live" : "Paused");
}

/* ---------- Application ---------- */

static void activate(GtkApplication *gapp, gpointer data)
{
  App *app = data;

  GtkWidget *window = gtk_application_window_new(gapp);
  gtk_window_set_title(GTK_WINDOW(window), "Radio");
  gtk_window_set_default_size(GTK_WINDOW(window), 800, 600);

  GtkWidget *box = gtk_box_new(GTK_ORIENTATION_VERTICAL, 12);
  gtk_widget_set_margin_top(box, 24);
  gtk_widget_set_margin_bottom(box, 12);
  gtk_widget_set_margin_start(box, 24);
  gtk_widget_set_margin_end(box, 24);
  gtk_container_add(GTK_CONTAINER(window), box);

  GtkWidget *title = gtk_label_new(NULL);
  gtk_label_set_markup(GTK_LABEL(title),
                       "<span size='xx-large' weight='bold'>BBC World Service</span>");
  gtk_box_pack_start(GTK_BOX(box), title, FALSE, FALSE, 0);

  app->status_label = gtk_label_new("Connecting\u2026");
  gtk_box_pack_start(GTK_BOX(box), app->status_label, FALSE, FALSE, 0);

  app->play_button = gtk_button_new_with_label("Pause");
  gtk_widget_set_halign(app->play_button, GTK_ALIGN_CENTER);
  g_signal_connect(app->play_button, "clicked", G_CALLBACK(on_play_clicked), app);
  gtk_box_pack_start(GTK_BOX(box), app->play_button, FALSE, FALSE, 0);

  /* Spacer pushes the ticker to the bottom */
  GtkWidget *spacer = gtk_box_new(GTK_ORIENTATION_VERTICAL, 0);
  gtk_box_pack_start(GTK_BOX(box), spacer, TRUE, TRUE, 0);

  app->ticker_label = gtk_label_new("Loading headlines\u2026");
  gtk_style_context_add_class(gtk_widget_get_style_context(app->ticker_label),
                              "monospace");
  gtk_label_set_xalign(GTK_LABEL(app->ticker_label), 0.0);
  gtk_box_pack_start(GTK_BOX(box), app->ticker_label, FALSE, FALSE, 0);

  /* Audio */
  app->playbin = gst_element_factory_make("playbin", "player");
  if (!app->playbin) {
    gtk_label_set_text(GTK_LABEL(app->status_label), "GStreamer playbin not available");
  } else {
    g_object_set(app->playbin, "uri", STREAM_URI, NULL);
    GstBus *bus = gst_element_get_bus(app->playbin);
    app->bus_watch_id = gst_bus_add_watch(bus, on_bus_message, app);
    gst_object_unref(bus);
    gst_element_set_state(app->playbin, GST_STATE_PLAYING);
    app->playing = TRUE;
  }

  /* News */
  app->session = soup_session_new();
  app->cancel = g_cancellable_new();
  refresh_feed(app);
  app->refresh_id = g_timeout_add_seconds(REFRESH_SECONDS, refresh_feed, app);
  app->tick_id = g_timeout_add(TICKER_MS, on_tick, app);

  gtk_widget_show_all(window);
}

static void shutdown_app(GApplication *gapp, gpointer data)
{
  App *app = data;
  if (app->tick_id)    g_source_remove(app->tick_id);
  if (app->refresh_id) g_source_remove(app->refresh_id);
  if (app->cancel)     { g_cancellable_cancel(app->cancel); g_clear_object(&app->cancel); }
  g_clear_object(&app->session);
  if (app->bus_watch_id) g_source_remove(app->bus_watch_id);
  if (app->playbin) {
    gst_element_set_state(app->playbin, GST_STATE_NULL);
    gst_object_unref(app->playbin);
    app->playbin = NULL;
  }
  g_free(app->ticker_text);
  app->ticker_text = NULL;
}

int main(int argc, char **argv)
{
  App app = {0};
  gst_init(&argc, &argv);

  GtkApplication *gapp = gtk_application_new("org.gnome.Radio", G_APPLICATION_DEFAULT_FLAGS);
  g_signal_connect(gapp, "activate", G_CALLBACK(activate), &app);
  g_signal_connect(gapp, "shutdown", G_CALLBACK(shutdown_app), &app);
  int status = g_application_run(G_APPLICATION(gapp), argc, argv);
  g_object_unref(gapp);
  return status;
}
