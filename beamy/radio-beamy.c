#include <goocanvas.h>
#include <gst/gst.h>

typedef struct {
    const char *name;
    const char *uri;
    double x;
    double y;
} Station;

static GstElement *player;

/* Example stations (you can add many) */
static Station stations[] = {
    { "C-SPAN", "https://playerservices.streamtheworld.com/api/livestream-redirect/CSPANRADIO.mp3", 150, 150 },
    { "BBC World Service", "http://stream.live.vc.bbcmedia.co.uk/bbc_world_service", 300, 200 },
    { "NRK Alltid Nyheter", "http://cdn0-47115-liveicecast0.dna.contentdelivery.net:80/nyheter_aac_h", 500, 250 }    
};

static void play_station(const char *uri)
{
    g_object_set(player, "uri", uri, NULL);
    gst_element_set_state(player, GST_STATE_PLAYING);
}

static gboolean on_circle_clicked(GooCanvasItem *item,
                                  GooCanvasItem *target,
                                  GdkEventButton *event,
                                  gpointer user_data)
{
    const char *uri = (const char *)user_data;
    g_print("Playing: %s\n", uri);
    gst_element_set_state(player, GST_STATE_NULL);    
    play_station(uri);
    return TRUE;
}

static GooCanvasItem* create_station_circle(GooCanvasItem *parent, Station *s)
{
    GooCanvasItem *circle = goo_canvas_ellipse_new(parent,
        s->x, s->y,
        20, 20,   // radius x, y
        "fill-color", "red",
        "stroke-color", "white",
        "line-width", 2.0,
        NULL);

    g_signal_connect(circle, "button-press-event",
                     G_CALLBACK(on_circle_clicked),
                     (gpointer)s->uri);

    /* Label */
    goo_canvas_text_new(parent,
        s->name,
        s->x, s->y + 30,
        -1,
        GTK_WIN_POS_CENTER,
        "font", "Sans 10",
        "fill-color", "white",
        NULL);

    return circle;
}

static void activate(GtkApplication *app, gpointer user_data)
{
    GtkWidget *window = gtk_application_window_new(app);
    gtk_window_set_title(GTK_WINDOW(window), "Beamy Radio");
    gtk_window_set_default_size(GTK_WINDOW(window), 800, 600);

    GtkWidget *canvas = goo_canvas_new();
    gtk_container_add(GTK_CONTAINER(window), canvas);

    goo_canvas_set_bounds(GOO_CANVAS(canvas), 0, 0, 800, 600);

    GooCanvasItem *root = goo_canvas_get_root_item(GOO_CANVAS(canvas));

    /* Background */
    goo_canvas_rect_new(root,
        0, 0, 800, 600,
        "fill-color", "black",
        NULL);

    /* Draw stations */
    int count = sizeof(stations) / sizeof(Station);
    for (int i = 0; i < count; i++) {
        create_station_circle(root, &stations[i]);
    }

    gtk_widget_show_all(window);
}

int main(int argc, char *argv[])
{
    gst_init(&argc, &argv);

    player = gst_element_factory_make("playbin", "player");

    GtkApplication *app = gtk_application_new(
        "org.gnomeradio.beamyradio",
        G_APPLICATION_FLAGS_NONE
    );

    g_signal_connect(app, "activate", G_CALLBACK(activate), NULL);

    int status = g_application_run(G_APPLICATION(app), argc, argv);

    gst_element_set_state(player, GST_STATE_NULL);
    gst_object_unref(player);
    g_object_unref(app);

    return status;
}
